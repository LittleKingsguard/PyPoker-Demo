"""Deep-scale integration run: best-chips card model (tok-60) driving a policy head.
Args: <zero|card> <seed> <train_hands>  -- writes a json line with chips and the loaded-deal table."""
import numpy as np, torch, torch.nn as nn, collections, random, json, sys, engine, agents
ZERO = sys.argv[1]=='zero'; SEED=int(sys.argv[2]); TRAIN=int(sys.argv[3]); EVAL=2000
SH='six-seat-no-limit-100'; RANKS='23456789TJQKA'; SUITS='cdhs'
POS=torch.arange(7).unsqueeze(0)
class AttnTok(nn.Module):
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
sd=torch.load('.probe/attn60.pt'); remap={'pos.':'posemb.','n1.':'norm.','n2.':'ffn.'}
fixed={}
for k,v in sd.items():
    for a,b in remap.items():
        if k.startswith(a): k=b+k[len(a):]; break
    fixed[k]=v
sup=AttnTok(); sup.load_state_dict(fixed); sup.eval()
for p_ in sup.parameters(): p_.requires_grad_(False)
ACTIONS=('fold','check-call','raise-quarter','raise-half','raise-all-in','raise-minimum')
STREET={'preflop':0.0,'flop':1.0,'turn':2.0,'river':3.0}
f1=agents.build_baseline('fold-no-pair-or-face',0); f2=agents.build_baseline('fold-no-pair-or-better',0)
caller=agents.build_baseline('always-call',0)
class Policy(nn.Module):
    def __init__(s,a=6): super().__init__(); s.q=nn.Sequential(nn.Linear(56,64),nn.ReLU(),nn.Linear(64,64),nn.ReLU(),nn.Linear(64,a))
    def forward(s,x): return s.q(x)
def cards7(r):
    v=[0]*7
    for i,c in enumerate(list(r['hole'])+list(r['board'])):
        if i<7: v[i]=1+4*RANKS.index(str(c)[0])+SUITS.index(str(c)[1])
    t=torch.tensor([v]); return t,(t!=0)
def feats(r):
    ids,present=cards7(r)
    with torch.no_grad(): pooled,pwin=sup(ids)
    if ZERO: pooled=torch.zeros_like(pooled); pwin=torch.zeros_like(pwin)
    facts=torch.tensor([[r['pot']/600.0, r['to_call']/100.0, STREET[r['street']]/3.0,
                         r['stacks'][r['seat'][0]]/100.0, len(r['board'])/5.0]], dtype=torch.float32)
    return torch.cat([pooled,pwin,facts],dim=1)
torch.manual_seed(SEED); random.seed(SEED)
pol=Policy(); opt=torch.optim.Adam(pol.parameters(),1e-3)
def policy(eps):
    def f(r, legal):
        idxs=[ACTIONS.index(a) for a in r['legal']]
        if random.random()<eps: i=random.choice(idxs)
        else:
            x=feats(r)
            with torch.no_grad(): q=pol(x)[0]
            i=max(idxs, key=lambda j: float(q[j]))
        return ACTIONS[i]
    return f
base = 3_000_000 + SEED*100_000 + (500_000 if ZERO else 0)
for h in range(TRAIN):
    eps=max(0.05, 1.0-h/(TRAIN*0.5)); k=h%5
    pols=[f1,f2,caller,f1,f2]; pols.insert(k, policy(eps))
    res=engine.play_hand(base+h, shape=SH, seats=tuple(pols))
    net=res['payoffs'][k]/600.0
    for d in res['decisions']:
        if d['seat'][0]!=k: continue
        x=feats(d['readout']); idx=ACTIONS.index(d['action'])
        with torch.no_grad(): qv=float(pol(x)[0][idx])
        pol(x)[0][idx].backward()
        for p_ in pol.parameters(): p_.grad *= -2.0*(net-qv)
        opt.step(); opt.zero_grad()
g=policy(0.0); chips=[]; acts=collections.Counter()
for h in range(EVAL):
    k=h%5; pols=[f1,f2,caller,f1,f2]; pols.insert(k,g)
    res=engine.play_hand(base+900_000+h, shape=SH, seats=tuple(pols))
    chips.append(res['payoffs'][k])
    for d in res['decisions']:
        if d['seat'][0]==k: acts[d['action']]+=1
DRY=["3s","6d","9d","4c","Jh"]; FILL=[("3c","4d"),("Jc","Td"),("3h","5h"),("4s","6c"),("5d","6s")]
def deal(hole, seat=3):
    holes=[]; q=0
    for s in range(6):
        if s==seat: holes.append(list(hole))
        else: holes.append(list(FILL[q])); q+=1
    return {"holes":holes,"board":list(DRY)}
table={}
for name,hole in (("AA",("As","Ad")),("KQs",("Ks","Qs")),("22",("2s","2h")),("87s",("8s","7s")),("72o",("7c","2d"))):
    r=engine.play_hand(20261115, shape=SH, seats=(f1,caller,f2,g,f1,f2), deal=deal(hole))
    table[name]=[d['action'] for d in r['decisions'] if d['seat'][0]==3][:2]
m=float(np.mean(chips)); ci=2*float(np.std(chips))/len(chips)**0.5
tot=sum(acts.values()) or 1
print(json.dumps({'arm':'zero' if ZERO else 'card','seed':SEED,'hands':EVAL,'chips':round(m,3),'ci':round(ci,3),
                  'distinct':len({tuple(v) for v in table.values()}),'census':{k:round(100*v/tot,1) for k,v in acts.items()},
                  'table':table}))
