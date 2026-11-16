"""Fast integration probe against the LEAGUE pool.
Fix vs the deep run: features and actions are gathered during play with no_grad, then ONE batched
forward+backward+step per hand -- instead of a backward and Adam step for every decision.
Args: <card|zero> <seed> <train_hands>"""
import numpy as np, torch, torch.nn as nn, collections, random, json, sys, engine, agents, evaluation
ZERO=sys.argv[1]=='zero'; SEED=int(sys.argv[2]); TRAIN=int(sys.argv[3]); EVAL=2000
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
LEAGUE=[  # three distinct behaviours, all six-seat capable
 '/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt',        # 100% fold
 '/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt',        # 50% fold / 50% raise
 '/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt',              # 83% raise
]
leaguers=[evaluation.policy_from(p, exploration='off') for p in LEAGUE]
caller=agents.build_baseline('always-call',0)
ACTIONS=('fold','check-call','raise-quarter','raise-half','raise-all-in','raise-minimum')
STREET={'preflop':0.0,'flop':1.0,'turn':2.0,'river':3.0}
class Policy(nn.Module):
    def __init__(s,a=6): super().__init__(); s.q=nn.Sequential(nn.Linear(56,64),nn.ReLU(),nn.Linear(64,64),nn.ReLU(),nn.Linear(64,a))
    def forward(s,x): return s.q(x)
def cards7(r):
    v=[0]*7
    for i,c in enumerate(list(r['hole'])+list(r['board'])):
        if i<7: v[i]=1+4*RANKS.index(str(c)[0])+SUITS.index(str(c)[1])
    return torch.tensor([v])
def feats(r):
    ids=cards7(r)
    with torch.no_grad(): pooled,pwin=sup(ids)
    if ZERO: pooled=torch.zeros_like(pooled); pwin=torch.zeros_like(pwin)
    facts=torch.tensor([[r['pot']/600.0, r['to_call']/100.0, STREET[r['street']]/3.0,
                         r['stacks'][r['seat'][0]]/100.0, len(r['board'])/5.0]], dtype=torch.float32)
    return torch.cat([pooled,pwin,facts],dim=1)
torch.manual_seed(SEED); random.seed(SEED)
pol=Policy(); opt=torch.optim.Adam(pol.parameters(),1e-3)
def opponents(seat):
    """five opponents: the league members and one scripted caller, rotated by seat."""
    out=[]
    for s in range(6):
        if s==seat: out.append(None)
        else: out.append(leaguers[(s+seat)%3] if (s+seat)%5 else caller)
    return out
def play(seed, seat, eps, learn):
    cache=[]; acts=[]
    opp=opponents(seat)
    def mine(r, legal):
        idxs=[ACTIONS.index(a) for a in r['legal']]; x=feats(r)
        if random.random()<eps: i=random.choice(idxs)
        else:
            with torch.no_grad(): q=pol(x)[0]
            i=max(idxs, key=lambda j: float(q[j]))
        cache.append(x); acts.append(i)
        return ACTIONS[i]
    seats=[mine if s==seat else opp[s] for s in range(6)]
    res=engine.play_hand(seed, shape=SH, seats=tuple(seats))
    if learn and cache:
        X=torch.cat(cache); tgt=res['payoffs'][seat]/600.0
        q=pol(X)[torch.arange(len(acts)), torch.tensor(acts)]
        loss=((q-tgt)**2).mean()          # ONE batched update per hand
        opt.zero_grad(); loss.backward(); opt.step()
    return res
base=5_000_000+SEED*100_000+(500_000 if ZERO else 0)
for h in range(TRAIN):
    play(base+h, h%5, max(0.05, 1.0-h/(TRAIN*0.5)), True)
chips=[]; census=collections.Counter()
import time; t0=time.time()
for h in range(EVAL):
    res=play(base+900_000+h, h%5, 0.0, False)
    chips.append(res['payoffs'][h%5])
    for d in res['decisions']:
        if d['seat'][0]==h%5: census[d['action']]+=1
el=time.time()-t0
m=float(np.mean(chips)); ci=2*float(np.std(chips))/len(chips)**0.5
tot=sum(census.values()) or 1
print(json.dumps({'arm':'zero' if ZERO else 'card','seed':SEED,'hands':EVAL,'chips':round(m,3),'ci':round(ci,3),
                  'census':{k:round(100*v/tot,1) for k,v in census.most_common()},
                  'eval_sec_per_hand':round(el/EVAL*1000,1)}))
