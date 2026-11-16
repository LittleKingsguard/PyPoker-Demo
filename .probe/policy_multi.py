"""Same policy head, same opponents, same hands -- driven by three different card models.
Compares (a) play quality (chips/hand, greedy), (b) card-dependence on the loaded-deal suite."""
import numpy as np, torch, torch.nn as nn, collections, random, engine, agents
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
class AttnOne(nn.Module):
    def __init__(s,d=50,h=5,L=2,w=96):
        super().__init__(); s.proj=nn.Linear(17,d); s.posemb=nn.Embedding(7,d)
        s.mha=nn.ModuleList([nn.MultiheadAttention(d,h,batch_first=True) for _ in range(L)])
        s.norm=nn.ModuleList([nn.LayerNorm(d) for _ in range(L)]); s.ffn=nn.ModuleList([nn.LayerNorm(d) for _ in range(L)])
        s.ff=nn.ModuleList([nn.Sequential(nn.Linear(d,w),nn.ReLU(),nn.Linear(w,d)) for _ in range(L)])
        s.head=nn.Sequential(nn.Linear(d,w),nn.ReLU(),nn.Linear(w,w),nn.ReLU(),nn.Linear(w,1),nn.Sigmoid())
    def forward(s, ids, present):
        oh=torch.zeros(ids.shape[0],7,17)
        for b in range(ids.shape[0]):
            for j in range(7):
                i=int(ids[b,j])
                if i:
                    ri=(i-1)//4; si=(i-1)%4
                    oh[b,j,ri]=1.0; oh[b,j,13+si]=1.0
        pad=~present; h=s.proj(oh)+s.posemb(POS[:, :ids.shape[1]])
        for m,a,f,b in zip(s.mha,s.norm,s.ff,s.ffn):
            y,_=m(h,h,h,key_padding_mask=pad,need_weights=False); h=a(h+y); h=b(h+f(h))
        m=(~pad).unsqueeze(-1).float(); pooled=(h*m).sum(1)/m.sum(1).clamp(min=1.0)
        return pooled, s.head(pooled)
MODELS={'tok-60':('.probe/attn60.pt','tok'),'tok-400':('.probe/attnconv.pt','tok'),'onehot-200':('.probe/attn_onehot.pt','one')}
ACTIONS=('fold','check-call','raise-quarter','raise-half','raise-all-in','raise-minimum')
STREET={'preflop':0.0,'flop':1.0,'turn':2.0,'river':3.0}
f1=agents.build_baseline('fold-no-pair-or-face',0); f2=agents.build_baseline('fold-no-pair-or-better',0)
caller=agents.build_baseline('always-call',0)
class Policy(nn.Module):
    def __init__(s,a=6): super().__init__(); s.q=nn.Sequential(nn.Linear(56,64),nn.ReLU(),nn.Linear(64,64),nn.ReLU(),nn.Linear(64,a))
    def forward(s,x): return s.q(x)
def build(path, kind):
    m = AttnTok() if kind=='tok' else AttnOne()
    sd=torch.load(path)
    remap={'pos.':'posemb.','n1.':'norm.','n2.':'ffn.'}
    fixed={}
    for k,v in sd.items():
        for a,b in remap.items():
            if k.startswith(a): k=b+k[len(a):]; break
        fixed[k]=v
    m.load_state_dict(fixed); m.eval()
    for p_ in m.parameters(): p_.requires_grad_(False)
    return m
def cards7(r):
    v=[0]*7
    for i,c in enumerate(list(r['hole'])+list(r['board'])):
        if i<7: v[i]=1+4*RANKS.index(str(c)[0])+SUITS.index(str(c)[1])
    t=torch.tensor([v]); return t,(t!=0)
def run(tag, path, kind):
    card=build(path,kind)
    def feats(r):
        ids,present=cards7(r)
        with torch.no_grad(): pooled,pwin = card(ids) if kind=='tok' else card(ids,present)
        facts=torch.tensor([[r['pot']/600.0, r['to_call']/100.0, STREET[r['street']]/3.0,
                             r['stacks'][r['seat'][0]]/100.0, len(r['board'])/5.0]], dtype=torch.float32)
        return torch.cat([pooled,pwin,facts],dim=1)
    torch.manual_seed(0); pol=Policy(); opt=torch.optim.Adam(pol.parameters(),1e-3)
    def policy(eps):
        def f(r, legal):
            idxs=[ACTIONS.index(a) for a in r['legal']]; x=feats(r)
            if random.random()<eps: i=random.choice(idxs)
            else:
                with torch.no_grad(): q=pol(x)[0]
                i=max(idxs, key=lambda j: float(q[j]))
            return ACTIONS[i]
        return f
    random.seed(0)
    for h in range(4000):
        eps=max(0.05,1.0-h/2000); k=h%5
        pols=[f1,f2,caller,f1,f2]; pols.insert(k, policy(eps))
        res=engine.play_hand(900000+h, shape=SH, seats=tuple(pols))
        net=res['payoffs'][k]/600.0
        for d in res['decisions']:
            if d['seat'][0]!=k: continue
            x=feats(d['readout']); idx=ACTIONS.index(d['action'])
            with torch.no_grad(): qv=float(pol(x)[0][idx])
            pol(x)[0][idx].backward()
            for p_ in pol.parameters(): p_.grad *= -2.0*(net-qv)
            opt.step(); opt.zero_grad()
    g=policy(0.0); chips=[]
    random.seed(1)
    for h in range(500):
        k=h%5; pols=[f1,f2,caller,f1,f2]; pols.insert(k,g)
        chips.append(engine.play_hand(950000+h, shape=SH, seats=tuple(pols))['payoffs'][k])
    DRY=["3s","6d","9d","4c","Jh"]; FILL=[("3c","4d"),("Jc","Td"),("3h","5h"),("4s","6c"),("5d","6s")]
    def deal(hole, seat=3):
        holes=[]; q=0
        for s in range(6):
            if s==seat: holes.append(list(hole))
            else: holes.append(list(FILL[q])); q+=1
        return {"holes":holes,"board":list(DRY)}
    out={}
    for name,hole in (("AA",("As","Ad")),("KQs",("Ks","Qs")),("22",("2s","2h")),("87s",("8s","7s")),("72o",("7c","2d"))):
        r=engine.play_hand(20261115, shape=SH, seats=(f1,caller,f2,g,f1,f2), deal=deal(hole))
        out[name]=[d['action'] for d in r['decisions'] if d['seat'][0]==3][:2]
    m=float(np.mean(chips)); ci=2*float(np.std(chips))/len(chips)**0.5
    print(f"{tag:12} chips/hand {m:+7.3f} +/- {ci:5.3f}   distinct {len({tuple(v) for v in out.values()})}/5   " + "  ".join(f"{k}={v[0][:11] if v else '-'}" for k,v in out.items()), flush=True)
print("same head, same 4,000 hands, same opponents; only the card model differs")
for tag,(path,kind) in MODELS.items(): run(tag,path,kind)
