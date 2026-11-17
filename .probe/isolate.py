"""Which probe/product difference causes the collapse?  Three probe arms, same league, same seed:
  mc        baseline: every decision gets the hand's Monte-Carlo payoff (what the probe used)
  tdish     only the LAST decision of the hand gets the payoff, earlier ones get 0 (no credit)
  unmasked  the card representation is pooled over all 123 slots INCLUDING pads (the product's pooler)
"""
import numpy as np, torch, torch.nn as nn, collections, random, json, sys, engine, agents, evaluation
MODE=sys.argv[1]; SEED=0; TRAIN=5000; EVAL=2000
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
sd=torch.load('.probe/attn60.pt'); remap={'pos.':'posemb.','n1.':'norm.','n2.':'ffn.'}
fixed={}
for k,v in sd.items():
    for a,b in remap.items():
        if k.startswith(a): k=b+k[len(a):]; break
    fixed[k]=v
sup=Attn(); sup.load_state_dict(fixed); sup.eval()
for p_ in sup.parameters(): p_.requires_grad_(False)
LEAGUE=['/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt',
        '/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt',
        '/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt']
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
    if MODE=='unmasked':
        # the product's pooler: mean over ALL 123 slots, pads (row 0) included -> the card signal is diluted
        pad=torch.zeros(1,7,50)
        allrows=torch.cat([pooled.unsqueeze(1), pad.repeat(1,116,1)], dim=1)   # 117 pad slots of value 0
        pooled=allrows.mean(dim=1)
    facts=torch.tensor([[r['pot']/600.0, r['to_call']/100.0, STREET[r['street']]/3.0,
                         r['stacks'][r['seat'][0]]/100.0, len(r['board'])/5.0]], dtype=torch.float32)
    return torch.cat([pooled,pwin,facts],dim=1)
torch.manual_seed(SEED); random.seed(SEED)
pol=Policy(); opt=torch.optim.Adam(pol.parameters(),1e-3)
def play(seed, seat, eps, learn):
    cache=[]; acts=[]
    def mine(r, legal):
        idxs=[ACTIONS.index(a) for a in r['legal']]; x=feats(r)
        if random.random()<eps: i=random.choice(idxs)
        else:
            with torch.no_grad(): q=pol(x)[0]
            i=max(idxs, key=lambda j: float(q[j]))
        cache.append(x); acts.append(i); return ACTIONS[i]
    seats=[mine if s==seat else (leaguers[(s+seat)%3] if (s+seat)%5 else caller) for s in range(6)]
    res=engine.play_hand(seed, shape=SH, seats=tuple(seats))
    if learn and cache:
        X=torch.cat(cache); net=res['payoffs'][seat]/600.0
        tgt=torch.full((len(acts),), net)
        if MODE=='tdish':
            tgt=torch.zeros(len(acts)); tgt[-1]=net        # only the last decision is credited
        q=pol(X)[torch.arange(len(acts)), torch.tensor(acts)]
        loss=((q-tgt)**2).mean(); opt.zero_grad(); loss.backward(); opt.step()
    return res
for h in range(TRAIN): play(5_100_000+h, h%5, max(0.05,1.0-h/(TRAIN*0.5)), True)
chips=[]; census=collections.Counter()
for h in range(EVAL):
    seat=h%5; res=play(5_900_000+h, seat, 0.0, False)
    chips.append(res['payoffs'][seat])
    for d in res['decisions']:
        if d['seat'][0]==seat: census[d['action']]+=1
tot=sum(census.values()) or 1
print(json.dumps({'mode':MODE,'chips':round(float(np.mean(chips)),3),
                  'ci':round(2*float(np.std(chips))/len(chips)**0.5,3),
                  'census':{k:round(100*v/tot,1) for k,v in census.most_common()}}))
