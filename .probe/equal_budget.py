"""Equal-budget (15,000 hands) probe comparison at the normalised scale, with trunk health measured.
MODE=mc   : every decision of the hand gets the hand's payoff (Monte-Carlo credit)
MODE=tdish: only the hand's last decision is credited, earlier ones get 0 (no credit propagation)"""
import numpy as np, torch, torch.nn as nn, collections, random, json, sys, engine, agents, evaluation
MODE=sys.argv[1]; SEED=0; TRAIN=15000; EVAL=2000
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
        m=(~pad).unsqueeze(-1).float(); pooled=(x*m).sum(1)/m.sum(1).clamp(min=1.0)
        return pooled, s.head(pooled)
sd=torch.load('.probe/attn60.pt'); remap={'pos.':'posemb.','n1.':'norm.','n2.':'ffn.'}
fx={}
for k,v in sd.items():
    for a,b in remap.items():
        if k.startswith(a): k=b+k[len(a):]; break
    fx[k]=v
sup=Attn(); sup.load_state_dict(fx); sup.eval()
for p_ in sup.parameters(): p_.requires_grad_(False)
LEAGUE=['/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt',
        '/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt',
        '/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt']
mix=[evaluation.policy_from(p, exploration='off') for p in LEAGUE]
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
    with torch.no_grad(): pooled,pwin=sup(cards7(r))
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
    seats=[mine if s==seat else (mix[(s+seat)%3] if (s+seat)%5 else caller) for s in range(6)]
    r=engine.play_hand(seed, shape=SH, seats=tuple(seats))
    if learn and cache:
        X=torch.cat(cache); net=r['payoffs'][seat]/600.0
        tgt=torch.full((len(acts),), net) if MODE=='mc' else torch.cat([torch.zeros(len(acts)-1), torch.tensor([net])])
        q=pol(X)[torch.arange(len(acts)), torch.tensor(acts)]
        loss=((q-tgt)**2).mean(); opt.zero_grad(); loss.backward(); opt.step()
    return r
for h in range(TRAIN): play(6_100_000+h, h%5, max(0.05,1.0-h/(TRAIN*0.5)), True)
torch.save(pol.state_dict(), f'.probe/eq-{MODE}.pt')
chips=[]; census=collections.Counter(); sd_hand=0; acts_by_pressure=collections.Counter(); folds_pressure=collections.Counter()
for h in range(EVAL):
    seat=h%5; r=play(6_900_000+h, seat, 0.0, False)
    chips.append(r['payoffs'][seat]); sd_hand += 1 if r['reveal']['showdown'] else 0
    for d in r['decisions']:
        if d['seat'][0]!=seat: continue
        census[d['action']]+=1
        press=d['readout']['to_call']>0; acts_by_pressure[press]+=1
        if d['action']=='fold': folds_pressure[press]+=1
# trunk health of the probe's own head
W1=pol.q[0].weight.detach().numpy(); b1=pol.q[0].bias.detach().numpy()
X=np.random.randn(300,56).astype('float32')   # generic probes are uninformative; use real states instead
real=[]
for h in range(120):
    seat=h%5; r=play(6_950_000+h, seat, 0.0, False)
    for d in r['decisions']:
        if d['seat'][0]==seat: real.append(feats(d['readout']).detach().numpy().ravel())
A=np.clip(np.asarray(real)@W1.T+b1, 0, None)
tot=sum(census.values()) or 1
print(json.dumps({'mode':MODE,'train':TRAIN,'chips':round(float(np.mean(chips)),3),
                  'ci':round(2*float(np.std(chips))/len(chips)**0.5,3),
                  'showdown':round(100*sd_hand/EVAL,1),
                  'fold_facing':round(100*folds_pressure[True]/max(1,acts_by_pressure[True]),1),
                  'fold_not_facing':round(100*folds_pressure[False]/max(1,acts_by_pressure[False]),1),
                  'census':{k:round(100*v/tot,1) for k,v in census.most_common(3)},
                  'trunk_alive_l1':int(((A>0).mean(axis=0)>0).sum()),'units':64,
                  'distinct_acts':int(len(np.unique(A.round(9),axis=0)))}))
