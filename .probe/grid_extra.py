"""Play the reference hands through the two saved probe policies (the best configs) and dump their action strings."""
import sys, json, random, numpy as np, torch, torch.nn as nn, engine, agents
sys.path.insert(0,'.probe')
from opp_perseat import Net as OppNet, tok_seat, pub as opp_pub, MAXT
SH='six-seat-no-limit-100'; RANKS='23456789TJQKA'; SUITS='cdhs'; POS=torch.arange(7).unsqueeze(0)
REF=json.load(open('.probe/grids.json'))['ref']
HAND=[("quad aces",("As","Ad"),["Ah","Ac","7d","5s","2h"]),("nut flush",("As","Qs"),["Js","9s","4s","2h","7d"]),
      ("ace-high straight",("As","Kd"),["Qc","Js","Th","2d","7c"]),("trip aces",("As","Ad"),["Ah","Kd","7c","5s","2c"]),
      ("pair of kings (dry)",("Kh","Kd"),["7c","5s","2c","9d","Jh"]),("2-3 offsuit junk",("2c","3d"),["8h","9s","Jd","Qh","Kc"]),
      ("2-7 offsuit junk",("2d","7c"),["8h","9s","Jd","Qh","Kc"]),("2-3 offsuit, all-high board",("2c","3d"),["Ah","Kd","Qc","Js","9h"])]
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
opp=OppNet(); opp.load_state_dict(torch.load('.probe/opp_seat.pt')); opp.eval()
ACTIONS=('fold','check-call','raise-quarter','raise-half','raise-all-in','raise-minimum')
STREET={'preflop':0.0,'flop':1.0,'turn':2.0,'river':3.0}
class Policy(nn.Module):
    def __init__(s,dim): super().__init__(); s.q=nn.Sequential(nn.Linear(dim,64),nn.ReLU(),nn.Linear(64,64),nn.ReLU(),nn.Linear(64,6))
    def forward(s,x): return s.q(x)
def feats(rd, myseat, use_opp):
    v=[0]*7
    for i,c in enumerate(list(rd['hole'])+list(rd['board'])):
        if i<7: v[i]=1+4*RANKS.index(str(c)[0])+SUITS.index(str(c)[1])
    with torch.no_grad(): pooled,pwin=card(torch.tensor([v]))
    parts=[pooled,pwin,torch.tensor([[rd['pot']/600.0, rd['to_call']/100.0, STREET[rd['street']]/3.0,
            rd['stacks'][rd['seat'][0]]/100.0, len(rd['board'])/5.0]],dtype=torch.float32)]
    if use_opp:
        last=None
        for e in reversed(rd['history']):
            p=e.split()
            if len(p)>=4: last=int(p[2]); break
        if last is None: parts.append(torch.zeros(1,3))
        else:
            tk=tok_seat(rd['history'], last); t=torch.tensor([tk+[0]*(MAXT-len(tk))])
            k=(last+myseat)%3 if (last+myseat)%5!=0 else None
            with torch.no_grad(): la=opp(t,torch.tensor([opp_pub(rd,k)],dtype=torch.float32))
            parts.append(torch.softmax(la,dim=1))
    return torch.cat(parts,dim=1)
f1=agents.build_baseline('fold-no-pair-or-face',0); f2=agents.build_baseline('fold-no-pair-or-better',0)
caller=agents.build_baseline('always-call',0)
def deal(hole, board, seat=3):
    used=set(hole)|set(board); rest=[r+s for r in RANKS for s in SUITS if r+s not in used]
    holes=[]; k=0
    for s in range(6):
        if s==seat: holes.append(list(hole))
        else: holes.append([rest[k],rest[k+1]]); k+=2
    return {"holes":holes,"board":list(board)}
def shorten(a): return 'f' if a=='fold' else ('c' if a=='check-call' else 'r')
out={}
for tag,arm,dim,use_opp in (("probe, eps 0.60","base",56,False),("probe, eps 0.60 + opponent","opp2",59,True)):
    net=Policy(dim); net.load_state_dict(torch.load(f'.probe/saved-{arm}-s0-eps0.6.pt')); net.eval()
    res={}
    for name,hole,board in HAND:
        def pol(r, legal, s=3):
            x=feats(r, s, use_opp)
            with torch.no_grad(): q=net(x)[0]
            return max(legal, key=lambda a: float(q[ACTIONS.index(a)]))
        r=engine.play_hand(20261115, shape=SH, seats=(f1,caller,f2,pol,f1,f2), deal=deal(hole,board))
        res[name]=''.join(shorten(d['action']) for d in r['decisions'] if d['seat'][0]==3) or '–'
    out[tag]=res
d=json.load(open('.probe/grids.json'))
d['results']['live'].update(out)
json.dump(d,open('.probe/grids.json','w'),indent=1)
for k,v in out.items(): print(k, v)
