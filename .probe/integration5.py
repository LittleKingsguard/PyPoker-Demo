"""base vs base + PER-SEAT opponent model.  The opponent's own history + identity drive the prediction."""
import sys, json, random, collections, numpy as np, torch, torch.nn as nn, engine, agents, evaluation
sys.path.insert(0,'.probe')
from opp_perseat import Net as OppNet, tok_seat, pub as opp_pub, MAXT, OPPS
ARM=sys.argv[1]; SEED=int(sys.argv[2]) if len(sys.argv)>2 else 0; TRAIN=5000; EVAL=2000
EPS=float(sys.argv[3]) if len(sys.argv)>3 else 0.05
USE_OPP = ARM=='opp2'
USE_NOISE = ARM=='noise'
USE_CONST = ARM=='const'
SH='six-seat-no-limit-100'; RANKS='23456789TJQKA'; SUITS='cdhs'; POS=torch.arange(7).unsqueeze(0)
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
        mask=(~pad).unsqueeze(-1).float(); pooled=(x*mask).sum(1)/mask.sum(1).clamp(min=1.0)
        return pooled, s.head(pooled)
sd=torch.load('.probe/attn60.pt'); rmap={'pos.':'posemb.','n1.':'norm.','n2.':'ffn.'}
fx={}
for k,v in sd.items():
    for a,b in rmap.items():
        if k.startswith(a): k=b+k[len(a):]; break
    fx[k]=v
card=Attn(); card.load_state_dict(fx); card.eval()
for p_ in card.parameters(): p_.requires_grad_(False)
opp=OppNet(); opp.load_state_dict(torch.load('.probe/opp_seat.pt')); opp.eval()
for p_ in opp.parameters(): p_.requires_grad_(False)
LEAGUE=['/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt',
        '/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt',
        '/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt']
mix=[evaluation.policy_from(p, exploration='off') for p in LEAGUE]
caller=agents.build_baseline('always-call',0)
ACTIONS=('fold','check-call','raise-quarter','raise-half','raise-all-in','raise-minimum')
STREET={'preflop':0.0,'flop':1.0,'turn':2.0,'river':3.0}
DIM=56+(3 if (USE_OPP or USE_NOISE or USE_CONST) else 0)
class Policy(nn.Module):
    def __init__(s,a=6): super().__init__(); s.q=nn.Sequential(nn.Linear(DIM,64),nn.ReLU(),nn.Linear(64,64),nn.ReLU(),nn.Linear(64,a))
    def forward(s,x): return s.q(x)
def ident_of(seat_of_s, my_seat):
    """identity index of the policy at seat s, mirroring how the seating was built."""
    return (seat_of_s+my_seat)%3 if (seat_of_s+my_seat)%5!=0 else None
def cards7(r):
    v=[0]*7
    for i,c in enumerate(list(r['hole'])+list(r['board'])):
        if i<7: v[i]=1+4*RANKS.index(str(c)[0])+SUITS.index(str(c)[1])
    return torch.tensor([v])
def feats(rd, my_seat):
    ids=cards7(rd)
    with torch.no_grad(): pooled,pwin=card(ids)
    parts=[pooled,pwin, torch.tensor([[rd['pot']/600.0, rd['to_call']/100.0, STREET[rd['street']]/3.0,
             rd['stacks'][rd['seat'][0]]/100.0, len(rd['board'])/5.0]], dtype=torch.float32)]
    if USE_CONST:                                 # three constant dimensions
        parts.append(torch.zeros(1,3))
    if USE_NOISE:                                 # three irrelevant but VARYING dimensions
        h=float(ids.sum()) % 97
        parts.append(torch.tensor([[np.sin(h), np.cos(h), np.sin(2*h)]], dtype=torch.float32))
    if USE_OPP:
        last=None
        for e in reversed(rd['history']):
            p=e.split()
            if len(p)>=4: last=int(p[2]); break
        if last is None:
            parts.append(torch.zeros(1,3))
        else:
            tk=tok_seat(rd['history'], last)
            t=torch.tensor([tk+[0]*(MAXT-len(tk))])
            k=ident_of(last, my_seat)
            pv=torch.tensor([opp_pub(rd, k)], dtype=torch.float32)
            with torch.no_grad(): la=opp(t,pv)
            parts.append(torch.softmax(la,dim=1))
    return torch.cat(parts, dim=1)
torch.manual_seed(SEED); random.seed(SEED)
pol=Policy(); opt=torch.optim.Adam(pol.parameters(),1e-3)
def play(seed, seat, eps, learn):
    cache=[]; acts=[]
    def mine(r, legal):
        idxs=[ACTIONS.index(a) for a in r['legal']]; x=feats(r, seat)
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
for h in range(TRAIN): play(7_500_000+h, h%5, max(EPS,1.0-h/(TRAIN*0.5)), True)
chips=[]; census=collections.Counter()
for h in range(EVAL):
    seat=h%5; r=play(8_100_000+h, seat, 0.0, False)
    chips.append(r['payoffs'][seat])
    for d in r['decisions']:
        if d['seat'][0]==seat: census[d['action']]+=1
tot=sum(census.values()) or 1
DRY=["3s","6d","9d","4c","Jh"]; HOLE=[("AA",("As","Ad")),("KQs",("Ks","Qs")),("22",("2s","2h")),("87s",("8s","7s")),("72o",("7c","2d"))]
f1=agents.build_baseline('fold-no-pair-or-face',0); f2=agents.build_baseline('fold-no-pair-or-better',0)
def deal(hole, seat=3):
    used=set(hole)|set(DRY); rest=[r+s for r in RANKS for s in SUITS if r+s not in used]
    holes=[]; k=0
    for s in range(6):
        if s==seat: holes.append(list(hole))
        else: holes.append([rest[k],rest[k+1]]); k+=2
    return {"holes":holes,"board":list(DRY)}
def greedy(rr, legal):
    idxs=[ACTIONS.index(a) for a in legal]; x=feats(rr, 3)
    with torch.no_grad(): q=pol(x)[0]
    return ACTIONS[max(idxs, key=lambda j: float(q[j]))]
tbl={}
for n,h in HOLE:
    r=engine.play_hand(20261115, shape=SH, seats=(f1,caller,f2,greedy,f1,f2), deal=deal(h))
    tbl[n]=[d['action'] for d in r['decisions'] if d['seat'][0]==3][:3]
torch.save(pol.state_dict(), f'.probe/saved-{ARM}-s{SEED}-eps{EPS}.pt')
# ---- D-116 monotonicity: aggression vs the hand's true preflop equity ----
import pokerkit as pk
DECK=[r+s for r in RANKS for s in SUITS]; CARD={c: list(pk.Card.parse(c))[0] for c in DECK}
LADDER=[("72o",("7c","2d")),("32o",("3c","2d")),("82o",("8c","2d")),("72s",("7c","2c")),("43s",("4c","3c")),
        ("87s",("8s","7s")),("T9s",("Ts","9s")),("22",("2s","2h")),("KQo",("Ks","Qd")),("AKo",("As","Kd")),
        ("QQ",("Qs","Qd")),("AA",("As","Ad"))]
def preflop_equity(hole, draws=300, seed=3):
    rnd=random.Random(seed); rest=[c for c in DECK if c not in hole]; w=0.0
    for _ in range(draws):
        pick=rnd.sample(rest,15); board=pick[:5]; others=pick[5:]
        mine=pk.StandardHighHand.from_game_or_none([CARD[c] for c in hole],[CARD[c] for c in board]).entry
        top=mine; ties=1
        for i in range(5):
            e=pk.StandardHighHand.from_game_or_none([CARD[c] for c in others[i*2:i*2+2]],[CARD[c] for c in board]).entry
            if e>top: ties=0; break
            if e==top: ties+=1
        if ties: w+=1.0/ties
    return w/draws
AGR={'fold':0,'check-call':1,'raise-minimum':2,'raise-quarter':2,'raise-half':2,'raise-all-in':2}
LBOARD=["5h","6h","9c","Jd","Th"]      # disjoint from every ladder hand
def ldeal(hole, seat=3):
    used=set(hole)|set(LBOARD); rest=[r+s for r in RANKS for s in SUITS if r+s not in used]
    holes=[]; k=0
    for s in range(6):
        if s==seat: holes.append(list(hole))
        else: holes.append([rest[k],rest[k+1]]); k+=2
    return {"holes":holes,"board":list(LBOARD)}
ladder=[]
for name,hole in LADDER:
    r=engine.play_hand(20262200, shape=SH, seats=(f1,caller,f2,greedy,f1,f2), deal=ldeal(hole))
    first=[d for d in r['decisions'] if d['seat'][0]==3 and d['readout']['street']=='preflop']
    ladder.append({'hand':name,'eq':round(preflop_equity(hole),4),'action':first[0]['action'] if first else None,
                   'aggr':AGR.get(first[0]['action'],1) if first else None})
pairs=[(a,b) for a,b in zip(ladder, ladder[1:])]
viol=sum(1 for i in range(len(ladder)) for j in range(len(ladder))
         if ladder[i]['eq']>ladder[j]['eq'] and ladder[i]['aggr']<ladder[j]['aggr'])
mono=all(ladder[k]['aggr']>=ladder[k-1]['aggr'] or ladder[k]['eq']<=ladder[k-1]['eq'] for k in range(1,len(ladder)))
print(json.dumps({'arm':ARM,'seed':SEED,'eps_floor':EPS,'chips':round(float(np.mean(chips)),3),
                  'card_dep':len({tuple(v) for v in tbl.values()}),
                  'ladder':[(d['hand'],round(100*d['eq'],1),d['action']) for d in ladder],
                  'violations':viol,'monotone_sorted_by_equity':mono}))
