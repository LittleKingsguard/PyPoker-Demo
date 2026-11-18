"""Adapter: expose a saved PROBE policy (a torch state dict from the integration runs) as a callable
policy with the same (readout, legal) -> action signature the engine and the browser table use.

These are not checkpoint containers: they are the integration experiments' saved heads, whose inputs are
the frozen attn-60 card model plus five table facts (and, for the top arms, the frozen per-seat opponent
model).  The browser table loads them through this module so the two best-measured policies are playable.
The probe's inputs are: the attn-60 card model's masked pooled representation + its strength, five
table facts, and optionally the per-seat opponent model's action probabilities."""

import os
import numpy as np
import torch
import torch.nn as nn

SHAPE = 'six-seat-no-limit-100'
RANKS = '23456789TJQKA'
SUITS = 'cdhs'
POS = torch.arange(7).unsqueeze(0)
STREET = {'preflop': 0.0, 'flop': 1.0, 'turn': 2.0, 'river': 3.0}
ACTIONS = ('fold', 'check-call', 'raise-quarter', 'raise-half', 'raise-all-in', 'raise-minimum')
MAXT = 32


class _Card(nn.Module):
    """The frozen attn-60 card model: pooled representation and win probability."""

    def __init__(self, d=50, h=5, layers=2, w=96):
        super().__init__()
        self.emb = nn.Embedding(53, d)
        self.posemb = nn.Embedding(7, d)
        self.mha = nn.ModuleList([nn.MultiheadAttention(d, h, batch_first=True) for _ in range(layers)])
        self.norm = nn.ModuleList([nn.LayerNorm(d) for _ in range(layers)])
        self.ffn = nn.ModuleList([nn.LayerNorm(d) for _ in range(layers)])
        self.ff = nn.ModuleList([nn.Sequential(nn.Linear(d, w), nn.ReLU(), nn.Linear(w, d)) for _ in range(layers)])
        self.head = nn.Sequential(nn.Linear(d, w), nn.ReLU(), nn.Linear(w, w), nn.ReLU(), nn.Linear(w, 1), nn.Sigmoid())

    def forward(self, ids):
        pad = ids == 0
        x = self.emb(ids) + self.posemb(POS[:, : ids.shape[1]])
        for m, a, f, b in zip(self.mha, self.norm, self.ff, self.ffn):
            y, _ = m(x, x, x, key_padding_mask=pad, need_weights=False)
            x = a(x + y)
            x = b(x + f(x))
        mask = (~pad).unsqueeze(-1).float()
        pooled = (x * mask).sum(1) / mask.sum(1).clamp(min=1.0)
        return pooled, self.head(pooled)


class _Opp(nn.Module):
    """The frozen per-seat opponent model."""

    def __init__(self, d=32, h=4, w=64, idents=4):
        super().__init__()
        self.emb = nn.Embedding(24, d)
        self.pos = nn.Embedding(MAXT, d)
        self.att = nn.MultiheadAttention(d, h, batch_first=True)
        self.n1 = nn.LayerNorm(d)
        self.ff = nn.Sequential(nn.Linear(d, w), nn.ReLU(), nn.Linear(w, d))
        self.n2 = nn.LayerNorm(d)
        self.pub = nn.Linear(5 + idents, d)
        self.act = nn.Linear(d, 3)

    def forward(self, tok, pub):
        pad = tok == 0
        x = self.emb(tok) + self.pos(torch.arange(tok.shape[1]).unsqueeze(0))
        a, _ = self.att(x, x, x, key_padding_mask=pad, need_weights=False)
        x = self.n1(x + a)
        x = self.n2(x + self.ff(x))
        m = (~pad).unsqueeze(-1).float()
        h = (x * m).sum(1) / m.sum(1).clamp(min=1.0)
        return self.act(h + self.pub(pub))


class _Head(nn.Module):
    def __init__(self, dim, actions=6):
        super().__init__()
        self.q = nn.Sequential(nn.Linear(dim, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, actions))

    def forward(self, x):
        return self.q(x)


def _cards(rd):
    v = [0] * 7
    for i, c in enumerate(list(rd['hole']) + list(rd['board'])):
        if i < 7:
            v[i] = 1 + 4 * RANKS.index(str(c)[0]) + SUITS.index(str(c)[1])
    return torch.tensor([v])


def _per_seat_tokens(history, seat):
    verbs = {'fold': 0, 'check': 1, 'call': 1, 'bet': 2, 'raise': 2}
    ids = []
    for i, e in enumerate(history):
        p = e.split()
        if len(p) < 4 or int(p[2]) != seat:
            continue
        amt = int(p[4]) if len(p) > 4 and p[4].isdigit() else 0
        ids += [1 + STREET.get(p[0], 0), 5 + verbs.get(p[3], 1),
                9 + (0 if amt == 0 else min(3, 1 + int(np.log2(amt)))), 13 + min(3, i % 4)]
    return ids[-MAXT:]


_HEADS: dict = {}
_MODELS: dict = {}


def _card_model(root):
    """The frozen attn-60 estimator, loaded once per process."""
    key = ('card', root)
    if key not in _MODELS:
        card = _Card()
        ckpt = torch.load(os.path.join(root, 'attn60.pt'), map_location='cpu', weights_only=True)
        remap = {'pos.': 'posemb.', 'n1.': 'norm.', 'n2.': 'ffn.'}
        fixed = {}
        for k, v in ckpt.items():
            for a, b in remap.items():
                if k.startswith(a):
                    k = b + k[len(a):]
                    break
            fixed[k] = v
        card.load_state_dict(fixed)
        card.eval()
        _MODELS[key] = card
    return _MODELS[key]


def _opp_model(root):
    """The frozen per-seat opponent model, loaded once per process."""
    key = ('opp', root)
    if key not in _MODELS:
        opp = _Opp()
        opp.load_state_dict(torch.load(os.path.join(root, 'opp_seat.pt'), map_location='cpu', weights_only=True))
        opp.eval()
        _MODELS[key] = opp
    return _MODELS[key]


def load(path, root='.probe'):
    """Build a callable policy from a saved probe state dict."""
    cached = _HEADS.get(path)
    if cached is not None:
        return cached
    state = torch.load(path, map_location='cpu', weights_only=True)
    dim = int(state['q.0.weight'].shape[1])
    uses_opp = dim >= 59
    head = _Head(dim)
    head.load_state_dict(state)
    head.eval()
    card = _card_model(root)
    opp = _opp_model(root) if uses_opp else None

    def policy(readout, legal):
        ids = _cards(readout)
        with torch.no_grad():
            pooled, pwin = card(ids)
        parts = [pooled, pwin,
                 torch.tensor([[readout['pot'] / 600.0, readout['to_call'] / 100.0,
                                STREET[readout['street']] / 3.0,
                                readout['stacks'][readout['seat'][0]] / 100.0,
                                len(readout['board']) / 5.0]], dtype=torch.float32)]
        if uses_opp:
            last = None
            for e in reversed(readout['history']):
                p = e.split()
                if len(p) >= 4:
                    last = int(p[2])
                    break
            if last is None:
                parts.append(torch.zeros(1, 3))
            else:
                tk = _per_seat_tokens(readout['history'], last)
                t = torch.tensor([tk + [0] * (MAXT - len(tk))], dtype=torch.long)
                seat = readout['seat'][0]
                ident = (last + seat) % 3 if (last + seat) % 5 != 0 else None
                pub = [readout['pot'] / 600.0, readout['to_call'] / 100.0, STREET[readout['street']] / 3.0,
                       len(readout['board']) / 5.0, readout['stacks'][readout['seat'][0]] / 100.0]
                pub += [1.0 if ident == k else 0.0 for k in range(4)]
                with torch.no_grad():
                    logits = opp(t, torch.tensor([pub], dtype=torch.float32))
                parts.append(torch.softmax(logits, dim=1))
        x = torch.cat(parts, dim=1)
        with torch.no_grad():
            q = head(x)[0]
        return max(legal, key=lambda a: float(q[ACTIONS.index(a)]))

    _HEADS[path] = policy
    return policy
