"""D-116's monotonicity test: is the policy's aggression non-decreasing in the hand's true equity?
Preflop decisions only -- the board is unknown then, so the decision sees exactly the hole cards."""
import sys, json, random, itertools, torch, torch.nn as nn, numpy as np, engine, agents
sys.path.insert(0,'.probe')
import pokerkit as pk
SH='six-seat-no-limit-100'; RANKS='23456789TJQKA'; SUITS='cdhs'; POS=torch.arange(7).unsqueeze(0)
DECK=[r+s for r in RANKS for s in SUITS]; CARD={c: list(pk.Card.parse(c))[0] for c in DECK}
LADDER=[("72o",("7c","2d")),("32o",("3c","2d")),("82o",("8c","2d")),("72s",("7c","2c")),("43s",("4c","3c")),
        ("87s",("8s","7s")),("T9s",("Ts","9s")),("22",("2s","2h")),("KQo",("Ks","Qd")),("AKo",("As","Kd")),
        ("QQ",("Qs","Qd")),("AA",("As","Ad"))]
def preflop_equity(hole, draws=400, seed=3):
    rnd=random.Random(seed); rest=[c for c in DECK if c not in hole]; w=0.0
    for _ in range(draws):
        pick=rnd.sample(rest, 5+10); board=pick[:5]; others=pick[5:]
        mine=pk.StandardHighHand.from_game_or_none([CARD[c] for c in hole],[CARD[c] for c in board]).entry
        top=mine; ties=1
        for i in range(5):
            e=pk.StandardHighHand.from_game_or_none([CARD[c] for c in others[i*2:i*2+2]],[CARD[c] for c in board]).entry
            if e>top: ties=0; break
            if e==top: ties+=1
        if ties: w+=1.0/ties
    return w/draws
AGR={'fold':0,'check-call':1,'raise-minimum':2,'raise-quarter':2,'raise-half':2,'raise-all-in':2}
def spearman(x,y):
    rx={v:i for i,v in enumerate(sorted(range(len(x)), key=lambda i:x[i]))}
    ry={v:i for i,v in enumerate(sorted(range(len(y)), key=lambda i:y[i]))}
    n=len(x); d=[rx[i]-ry[i] for i in range(n)]
    return 1-6*sum(v*v for v in d)/(n*(n*n-1))
class Attn(nn.Module):
    def __init__(s,d=50,h=5,L=2,w=96):
        super().__init__(); s.emb=nn.Embedding(53,d); s.posemb=nn.Embedding(7,d)
        s.mha=nn.ModuleList([nn.MultiheadAttention(d,h,batch_first=True) for _ in range(L)])
        s.norm=nn.ModuleList([nn.LayerNorm(d) for _ in range(L)]); s.ffn=nn.ModuleList([nn.LayerNorm(d) for _ in range(L)])
        s.ff=nn.ModuleList([nn.Sequential(nn.Linear(d,w),nn.ReLU(),nn.Linear(w,d)) for _ in range(L)])
        s.head=nn.Sequential(nn.Linear(d,w),nn.ReLU(),nn.Linear(w,w),nn.ReLU(),nn.Linear(w,1),nn.Sigmoid())
    def forward(s,ids):
        pad=ids==0; x=s.emb(ids)+s.posemb(POS[:, :ids.shape[1]])
        for m,a,f,b in zip(s.mha,s.norm,s.ff,s.ffn):
            y,_=m(x,x,x,key_padding_mask=pad,need_weights=False); x=a(x+y); x=b(x+f(x))
        m=(~pad).unsqueeze(-1).float(); pooled=(x*m).sum(1)/m.sum(1).clamp(min=1.0)
        return pooled, s.head(pooled)
sd=torch.load('.probe/attn60.pt'); rmap={'pos.':'posemb.','n1.':'norm.','n2.':'ffn.'}
fx={}
for k,v in sd.items():
    for a,b in rmap.items():
        if k.startswith(a): k=b+k[len(a):]; break
    fx[k]=v
card=Attn(); card.load_state_dict(fx); card.eval()
f1=agents.build_baseline('fold-no-pair-or-face',0); f2=agents.build_baseline('fold-no-pair-or-better',0)
caller=agents.build_baseline('always-call',0)
STREET={'preflop':0.0,'flop':1.0,'turn':2.0,'river':3.0}
def feats(rd):
    v=[0]*7
    for i,c in enumerate(list(rd['hole'])+list(rd['board'])):
        if i<7: v[i]=1+4*RANKS.index(str(c)[0])+SUITS.index(str(c)[1])
    with torch.no_grad(): pooled,pwin=card(torch.tensor([v]))
    facts=torch.tensor([[rd['pot']/600.0, rd['to_call']/100.0, STREET[rd['street']]/3.0,
                         rd['stacks'][rd['seat'][0]]/100.0, len(rd['board'])/5.0]], dtype=torch.float32)
    return torch.cat([pooled,pwin,facts],dim=1)
def make_policy(arm, seed, eps):
    net=torch.load(f'.probe/pol-{arm}-s{seed}-eps{eps}.pt', weights_only=False)
    def f(r, legal):
        x=feats(r)
        with torch.no_grad(): q=net(x)[0]
        return max([a for a in legal], key=lambda a: float(q[('fold','check-call','raise-quarter','raise-half','raise-all-in','raise-minimum').index(a)]))
    return f
print(f"{'hand':6} {'equity':>7}  aggression by arm")
eq={n:preflop_equity(h) for n,h in LADDER}
for n,h in LADDER: print(f"{n:6} {100*eq[n]:6.1f}%", end="")
print()
