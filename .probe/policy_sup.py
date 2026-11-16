"""Integrate the best card model into a policy: its pooled card representation AND its probability
estimate are inputs; the head learns Q-values over the six descriptors by masked-Q on the terminal
chip reward at six seats.  Then measure card-dependence on the loaded-deal suite."""
import numpy as np, torch, torch.nn as nn, collections, random, sys, engine, agents
ZERO = len(sys.argv)>1 and sys.argv[1]=='zero'
SH='six-seat-no-limit-100'; RANKS='23456789TJQKA'; SUITS='cdhs'
POS=torch.arange(7).unsqueeze(0)
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
sup=Attn(); sup.load_state_dict(torch.load('.probe/attnconv.pt')); sup.eval()
for p_ in sup.parameters(): p_.requires_grad_(False)
print(("ABLATION: card inputs zeroed" if ZERO else "card model loaded: pooled R2 40.0% (epoch 400)"))
def cards7(readout):
    v=[0]*7
    for i,c in enumerate(list(readout['hole'])+list(readout['board'])):
        if i<7: v[i]=1+4*RANKS.index(str(c)[0])+SUITS.index(str(c)[1])
    return torch.tensor([v], dtype=torch.long), (torch.tensor([v])!=0)
class Policy(nn.Module):
    """inputs: 50 (supervised pooled) + 1 (its probability) + 5 facts; outputs 6 Q-values."""
    def __init__(s,a=6):
        super().__init__(); s.q=nn.Sequential(nn.Linear(56,64),nn.ReLU(),nn.Linear(64,64),nn.ReLU(),nn.Linear(64,a))
    def forward(s,x): return s.q(x)
pol=Policy(); opt=torch.optim.Adam(list(pol.parameters()),1e-3)
ACTIONS=('fold','check-call','raise-quarter','raise-half','raise-all-in','raise-minimum')
STREET={'preflop':0.0,'flop':1.0,'turn':2.0,'river':3.0}
def facts(r):
    return torch.tensor([[r['pot']/600.0, r['to_call']/100.0, STREET[r['street']]/3.0,
                          r['stacks'][r['seat'][0]]/100.0, len(r['board'])/5.0]], dtype=torch.float32)
def state(r):
    ids,present=cards7(r)
    with torch.no_grad(): pooled,pwin=sup(ids)
    if ZERO: pooled=torch.zeros_like(pooled); pwin=torch.zeros_like(pwin)   # ablation: no card information
    return torch.cat([pooled, pwin, facts(r)], dim=1)
def legal_mask(r): return [ACTIONS.index(a) for a in r['legal']]
EPS=collections.defaultdict(float)
def make_policy(eps):
    def f(r, legal):
        idxs=legal_mask(r); x=state(r)
        if random.random()<eps: i=random.choice(idxs)
        else:
            with torch.no_grad(): q=pol(x)[0]
            i=max(idxs, key=lambda j: float(q[j]))
        return ACTIONS[i]
    return f
# opponents: two folders and a caller (scripted baselines)
f1=agents.build_baseline('fold-no-pair-or-face',0); f2=agents.build_baseline('fold-no-pair-or-better',0)
caller=agents.build_baseline('always-call',0)
print("training the policy with the card model's representation + probability ...", flush=True)
HANDS=4000
for h in range(HANDS):
    eps=max(0.05, 1.0-h/2000)
    seats=[f1,f2,caller,f1,f2]; k=h%5
    pols=seats[:]; pols.insert(k, make_policy(eps))
    res=engine.play_hand(900000+h, shape=SH, seats=tuple(pols))
    net=res['payoffs'][k]/600.0
    for d in res['decisions']:
        if d['seat'][0]!=k: continue
        x=state(d['readout']); q=pol(x)[0]
        idx=ACTIONS.index(d['action'])
        with torch.no_grad():
            target = net
            loss=(q[idx]-target)**2
        # one semi-gradient step on the chosen action's value
        opt.zero_grad(); pol(x)[0][idx].backward(); 
        for p_ in pol.parameters(): p_.grad *= -2.0*(target-float(q[idx].detach()))
        opt.step()
print("trained on", HANDS, "hands", flush=True)
# card dependence: loaded deals, the model at seat 3
DRY=["3s","6d","9d","4c","Jh"]; FILL=[("3c","4d"),("Jc","Td"),("3h","5h"),("4s","6c"),("5d","6s")]
def deal(hole, seat=3):
    holes=[]; k=0
    for s in range(6):
        if s==seat: holes.append(list(hole))
        else: holes.append(list(FILL[k])); k+=1
    return {"holes":holes,"board":list(DRY)}
HOLES=[("AA",("As","Ad")),("KQs",("Ks","Qs")),("22",("2s","2h")),("87s",("8s","7s")),("72o",("7c","2d"))]
polP=make_policy(0.0)
out={}
for name,hole in HOLES:
    r=engine.play_hand(20261115, shape=SH, seats=(f1,caller,f2,polP,f1,f2), deal=deal(hole))
    out[name]=[d['action'] for d in r['decisions'] if d['seat'][0]==3][:2]
print("greedy on the loaded-deal suite:", out)
print("distinct decisions:", len({tuple(v) for v in out.values()}), "of 5")
