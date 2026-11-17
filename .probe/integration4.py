"""Integrated test: masked card representation (attn-60) + strength + [bet_size] + [opponent model outputs].
Arms: base | bets | opp | full"""
import sys, json, random, collections, numpy as np, torch, torch.nn as nn, engine, agents, evaluation
sys.path.insert(0,'.probe')
from oppmodel import OppNet, tokenise, MAXH
ARM=sys.argv[1]; SEED=int(sys.argv[2]) if len(sys.argv)>2 else 0; TRAIN=5000; EVAL=2000
SH='six-seat-no-limit-100'; RANKS='23456789TJQKA'; SUITS='cdhs'; POS=torch.arange(7).unsqueeze(0)
USE_BET = ARM in ('bets','full'); USE_OPP = ARM in ('opp','full')
# ---- frozen card model (attn-60) ----
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
        mask=(~pad).unsqueeze(-1).float()
        pooled=(x*mask).sum(1)/mask.sum(1).clamp(min=1.0)     # MASKED pool == the product's fix
        return pooled, s.head(pooled)
sd=torch.load('.probe/attn60.pt'); rmap={'pos.':'posemb.','n1.':'norm.','n2.':'ffn.'}
fx={}
for k,v in sd.items():
    for a,b in rmap.items():
        if k.startswith(a): k=b+k[len(a):]; break
    fx[k]=v
card=Attn(); card.load_state_dict(fx); card.eval()
for p_ in card.parameters(): p_.requires_grad_(False)
opp=OppNet(); opp.load_state_dict(torch.load('.probe/opp.pt')); opp.eval()
for p_ in opp.parameters(): p_.requires_grad_(False)
LEAGUE=['/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt',
        '/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt',
        '/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt']
mix=[evaluation.policy_from(p, exploration='off') for p in LEAGUE]
caller=agents.build_baseline('always-call',0)
ACTIONS=('fold','check-call','raise-quarter','raise-half','raise-all-in','raise-minimum')
STREET={'preflop':0.0,'flop':1.0,'turn':2.0,'river':3.0}
DIM = 56 + (1 if USE_BET else 0) + (4 if USE_OPP else 0)
class Policy(nn.Module):
    def __init__(s,a=6):
        super().__init__(); s.q=nn.Sequential(nn.Linear(DIM,64),nn.ReLU(),nn.Linear(64,64),nn.ReLU(),nn.Linear(64,a))
    def forward(s,x): return s.q(x)
def cards7(r):
    v=[0]*7
    for i,c in enumerate(list(r['hole'])+list(r['board'])):
        if i<7: v[i]=1+4*RANKS.index(str(c)[0])+SUITS.index(str(c)[1])
    return torch.tensor([v])
def feats(rd):
    ids=cards7(rd)
    with torch.no_grad(): pooled,pwin=card(ids)
    parts=[pooled,pwin, torch.tensor([[rd['pot']/600.0, rd['to_call']/100.0, STREET[rd['street']]/3.0,
             rd['stacks'][rd['seat'][0]]/100.0, len(rd['board'])/5.0]], dtype=torch.float32)]
    if USE_BET:                                   # the fact the history block used to carry
        last=0.0
        for e in reversed(rd['history']):
            p=e.split()
            if len(p)>4 and p[4].isdigit(): last=int(p[4]); break
        parts.append(torch.tensor([[min(1.0, last/600.0)]], dtype=torch.float32))
    if USE_OPP:                                   # the opponent model's read of the current history
        t=torch.tensor([tokenise(rd['history'], len(rd['history']))+[0]*(MAXH-min(MAXH,len(rd['history'])*4))])
        pub=torch.tensor([[rd['pot']/600.0, rd['to_call']/100.0, STREET[rd['street']]/3.0,
                           len(rd['board'])/5.0, rd['stacks'][rd['seat'][0]]/100.0]+[0.0]*9], dtype=torch.float32)
        with torch.no_grad(): la,ls=opp(t,pub)
        parts.append(torch.softmax(la,dim=1)); parts.append(ls.reshape(1,1))
    return torch.cat(parts, dim=1)
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
    seats=[mine if s==seat else (mix[(s+seat)%3] if (s+seat)%5 else caller) for s in range(6)]
    r=engine.play_hand(seed, shape=SH, seats=tuple(seats))
    if learn and cache:
        X=torch.cat(cache); net=r['payoffs'][seat]/600.0
        q=pol(X)[torch.arange(len(acts)), torch.tensor(acts)]
        loss=((q-net)**2).mean(); opt.zero_grad(); loss.backward(); opt.step()
    return r
for h in range(TRAIN): play(7_300_000+h, h%5, max(0.05,1.0-h/(TRAIN*0.5)), True)
chips=[]; census=collections.Counter(); sdw=0
for h in range(EVAL):
    seat=h%5; r=play(7_900_000+h, seat, 0.0, False)
    chips.append(r['payoffs'][seat]); sdw += 1 if r['reveal']['showdown'] else 0
    for d in r['decisions']:
        if d['seat'][0]==seat: census[d['action']]+=1
tot=sum(census.values()) or 1
# card-dependence on the loaded-deal suite
DRY=["3s","6d","9d","4c","Jh"]; HOLE=[("AA",("As","Ad")),("KQs",("Ks","Qs")),("22",("2s","2h")),("87s",("8s","7s")),("72o",("7c","2d"))]
def deal(hole, seat=3):
    used=set(hole)|set(DRY); rest=[r+s for r in RANKS for s in SUITS if r+s not in used]
    holes=[]; k=0
    for s in range(6):
        if s==seat: holes.append(list(hole))
        else: holes.append([rest[k],rest[k+1]]); k+=2
    return {"holes":holes,"board":list(DRY)}
f1=agents.build_baseline('fold-no-pair-or-face',0); f2=agents.build_baseline('fold-no-pair-or-better',0)
tbl={}
for n,h in HOLE:
    r=engine.play_hand(20261115, shape=SH, seats=(f1,caller,f2,lambda rr,l: play_choice(rr,l),f1,f2), deal=deal(h)) if False else None
# deterministic replay of the trained policy on the loaded deals
def greedy_policy(rr, legal):
    idxs=[ACTIONS.index(a) for a in legal]; x=feats(rr)
    with torch.no_grad(): q=pol(x)[0]
    return ACTIONS[max(idxs, key=lambda j: float(q[j]))]
for n,h in HOLE:
    r=engine.play_hand(20261115, shape=SH, seats=(f1,caller,f2,greedy_policy,f1,f2), deal=deal(h))
    tbl[n]=[d['action'] for d in r['decisions'] if d['seat'][0]==3][:3]
print(json.dumps({'arm':ARM,'dim':DIM,'chips':round(float(np.mean(chips)),3),
                  'ci':round(2*float(np.std(chips))/len(chips)**0.5,3),'showdown':round(100*sdw/EVAL,1),
                  'census':{k:round(100*v/tot,1) for k,v in census.most_common(3)},
                  'card_dep':len({tuple(v) for v in tbl.values()}),'table':tbl}))
