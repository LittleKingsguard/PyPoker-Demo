"""Opponent model: an attention model over a seat's action history predicting
   (a) that seat's next action family (fold / call / raise) and (b) its hand strength.
Opponents include noisy variants of the scripted folders that ignore the fold rule and raise with probability p."""
import re, random, sys, json, collections, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
import engine, agents

SEATS=6; SH='six-seat-no-limit-100'; MAXH=24
VERBS={'fold':0,'check':1,'call':1,'bet':2,'raise':2}
STREETS={'preflop':0,'flop':1,'turn':2,'river':3}
ACT3={'fold':0,'check-call':1,'raise-minimum':2,'raise-quarter':2,'raise-half':2,'raise-all-in':2}

class NoisyFolder:
    """A scripted folder that, with probability p, ignores its rule and raises instead."""
    def __init__(self, name, p, seed):
        self.base=agents.build_baseline(name, seed); self.p=p; self.rng=random.Random(seed*7919+int(p*1000))
    def __call__(self, readout, legal):
        a=self.base(readout, legal)
        if a=='fold' and self.rng.random()<self.p:
            raises=[x for x in legal if x.startswith('raise')]
            if raises: return self.rng.choice(raises)
        return a

def tokenise(history, upto):
    """4 tokens per entry: street, seat, verb, amount bucket. Zero-filled to MAXH; 0 = pad."""
    ids=[]
    for entry in history[:upto]:
        parts=entry.split()                     # e.g. 'preflop seat 3 calls 2'
        st=STREETS.get(parts[0],0); seat=int(parts[2]); verb=VERBS.get(parts[3],1)
        amt=int(parts[4]) if len(parts)>4 and parts[4].isdigit() else 0
        b=0 if amt==0 else min(3, 1+int(np.log2(amt)))
        ids += [1+st, 7+seat, 13+verb, 16+b]
    return ids[:MAXH]

VARIANTS=[(n,p) for n in ('fold-no-pair-or-face','fold-no-pair-or-better','fold-large-bet') for p in (0.0,0.25,0.5)]
def public(readout, variant=None):
    base=[readout['pot']/600.0, readout['to_call']/100.0, STREETS[readout['street']]/3.0,
          len(readout['board'])/5.0, readout['stacks'][readout['seat'][0]]/100.0]
    ident=[0.0]*len(VARIANTS)
    if variant is not None and variant in VARIANTS: ident[VARIANTS.index(variant)]=1.0   # cross-hand proxy
    return base+ident

def collect(n_hands, seed):
    """Play hands and record, for every decision of every seat, its history, action and (later) its equity."""
    rng=random.Random(seed); rows=[]
    variants=[(n,p) for n in ('fold-no-pair-or-face','fold-no-pair-or-better','fold-large-bet') for p in (0.0,0.25,0.5)]
    caller=agents.build_baseline('always-call',0)
    for h in range(n_hands):
        picks=[variants[rng.randrange(len(variants))] for _ in range(SEATS)]
        seats=[NoisyFolder(n,p, seed*1000+h*SEATS+s) for s,(n,p) in enumerate(picks)]
        if h%3==0: seats[rng.randrange(SEATS)]=caller
        r=engine.play_hand(seed*1_000_000+h, shape=SH, seats=tuple(seats))
        holes={s['seat']: s['hole'] for s in r['reveal']['seats']}
        board=r['reveal']['board']
        for d in r['decisions']:
            seat=d['seat'][0]; rd=d['readout']
            rows.append({'tok':tokenise(rd['history'], len(rd['history'])), 'pub':public(rd, picks[seat]),
                         'y':ACT3.get(d['action'],1), 'seat':seat, 'hole':holes.get(seat),
                         'board_known':list(rd['board']), 'board':board, 'variant':picks[seat]})
    return rows

class OppNet(nn.Module):
    def __init__(s, d=32, heads=4, w=64):
        super().__init__(); s.emb=nn.Embedding(24, d); s.pos=nn.Embedding(MAXH, d)
        s.att=nn.MultiheadAttention(d, heads, batch_first=True); s.n1=nn.LayerNorm(d)
        s.ff=nn.Sequential(nn.Linear(d,w),nn.ReLU(),nn.Linear(w,d)); s.n2=nn.LayerNorm(d)
        s.pub=nn.Linear(5+len(VARIANTS),d)
        s.act=nn.Linear(d,3); s.str_=nn.Linear(d,1)
    def forward(s, tok, pub):
        pad=tok==0; x=s.emb(tok)+s.pos(torch.arange(tok.shape[1]).unsqueeze(0))
        a,_=s.att(x,x,x,key_padding_mask=pad,need_weights=False); x=s.n1(x+a); x=s.n2(x+s.ff(x))
        m=(~pad).unsqueeze(-1).float(); pooled=(x*m).sum(1)/m.sum(1).clamp(min=1.0)
        h=pooled+s.pub(pub)
        return s.act(h), s.str_(h).squeeze(-1)

if __name__=='__main__':
    N=int(sys.argv[1]) if len(sys.argv)>1 else 1200
    print(f"collecting {N} hands of 6-seat play with noisy folders ...", flush=True)
    rows=collect(N, 11)
    print("decision rows:", len(rows), "| action mix:",
          {k: round(100*v/len(rows),1) for k,v in collections.Counter(r['y'] for r in rows).items()}, flush=True)
    # strength labels: equity of the revealed hole+board against 5 random hands (Monte Carlo, 120 draws)
    import pokerkit as pk
    RANKS='23456789TJQKA'; SUITS='cdhs'; DECK=[r+s for r in RANKS for s in SUITS]
    CARD={c: list(pk.Card.parse(c))[0] for c in DECK}
    def equity(hole, board, draws=120, seed=5):
        """Equity against 5 random hands, integrating over the cards not yet dealt."""
        rnd=random.Random(seed); fixed=set(hole)|set(board)
        rest=[c for c in DECK if c not in fixed]; need=5-len(board); w=0.0
        for _ in range(draws):
            pick=rnd.sample(rest, need+10)
            full=list(board)+pick[:need]; others=pick[need:]
            mine=pk.StandardHighHand.from_game_or_none([CARD[c] for c in hole],[CARD[c] for c in full]).entry
            top=mine; ties=1
            for i in range(5):
                e=pk.StandardHighHand.from_game_or_none([CARD[c] for c in others[i*2:i*2+2]],[CARD[c] for c in full]).entry
                if e>top: ties=0; break
                if e==top: ties+=1
            if ties: w+=1.0/ties
        return w/draws
    for r in rows:
        r['eq']=equity(r['hole'], r['board_known'])     # the information the opponent had, not the run-out
    rows=[r for r in rows if r['eq'] is not None]
    print("rows with a strength label:", len(rows), flush=True)
    tok=torch.tensor([r['tok']+[0]*(MAXH-len(r['tok'])) for r in rows]); pub=torch.tensor([r['pub'] for r in rows], dtype=torch.float32)
    y=torch.tensor([r['y'] for r in rows]); s_=torch.tensor([r['eq'] for r in rows], dtype=torch.float32)
    n=len(rows); perm=np.random.default_rng(1).permutation(n); cut=int(n*.85)
    tr,te=perm[:cut],perm[cut:]
    torch.manual_seed(0); net=OppNet(); opt=torch.optim.Adam(net.parameters(),2e-3)
    for ep in range(1,13):
        p=torch.randperm(len(tr))
        for i in range(0,len(tr),1024):
            b=tr[p[i:i+1024]]
            la,ls=net(tok[b],pub[b])
            loss=F.cross_entropy(la,y[b],weight=torch.tensor([6.0,1.0,8.0]))+2.0*F.mse_loss(ls,s_[b])
            opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad():
        la,ls=net(tok[te],pub[te]); pred=la.argmax(1)
        acc=float((pred==y[te]).float().mean())
        base=float((torch.full_like(y[te], torch.bincount(y[tr]).argmax())==y[te]).float().mean())
        r2=1-float(((ls-s_[te])**2).mean())/float(((s_[te]-s_[te].mean())**2).mean())
        per={}
        for c,name in ((0,'fold'),(1,'call'),(2,'raise')):
            m=y[te]==c; n_c=int(m.sum())
            if n_c:
                tp=int((pred[m]==c).sum())
                per[name]={'n':n_c,'recall':round(tp/n_c,3),'precision':round(tp/max(1,int((pred==c).sum())),3),
                           'base_rate':round(float((torch.bincount(y[tr]).argmax()==c).float()),3)}
    print(json.dumps({'rows':n,'held_out':len(te),'action_acc':round(acc,4),'base_rate_acc':round(base,4),
                      'lift':round(acc-base,4),'strength_r2':round(r2,4),'per_class':per}))
