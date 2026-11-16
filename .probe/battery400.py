import numpy as np, torch, torch.nn as nn, sys
SRC=sys.argv[1] if len(sys.argv)>1 else '.probe/attnconv.pt'
RANKS='23456789TJQKA'; SUITS='cdhs'
X=np.load('/tmp/es_X.npy'); Y=np.load('/tmp/es_Y.npy').astype('float32'); S=np.load('/tmp/es_S.npy')
B7=X.reshape(-1,7,17); zero=B7.max(axis=2)==0
r=B7[:,:,:13].argmax(axis=2); s=B7[:,:,13:].argmax(axis=2)
Ids=(1+4*r+s).astype(np.int64); Ids[zero]=0
perm=np.random.default_rng(1).permutation(len(Ids)); cut=int(len(Ids)*.85)
Ite=torch.from_numpy(Ids[perm[cut:]]); Yte=torch.from_numpy(Y[perm[cut:]].reshape(-1,1)); Ste=S[perm[cut:]]
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
        m=(~pad).unsqueeze(-1).float(); return s.head((x*m).sum(1)/m.sum(1).clamp(min=1.0))
net=Attn(); net.load_state_dict(torch.load(SRC)); net.eval()
with torch.no_grad():
    pred=net(Ite); tot=100*(1-float(((pred-Yte)**2).mean())/float(((Yte-Yte.mean())**2).mean()))
    per={}
    for st in (3,4,5):
        m=(Ste==st); per[st]=100*(1-float(((pred[m]-Yte[m])**2).mean())/float(((Yte[m]-Yte[m].mean())**2).mean()))
print(f"checkpoint {SRC}: held-out pooled {tot:.2f}%   flop {per[3]:.2f}%  turn {per[4]:.2f}%  river {per[5]:.2f}%")
SCEN=[("quad aces",("As","Ad"),["Ah","Ac","7d","5s","2h"],100.00),
      ("nut flush",("As","Qs"),["Js","9s","4s","2h","7d"],100.00),
      ("ace-high straight",("As","Kd"),["Qc","Js","Th","2d","7c"],97.77),
      ("trip aces",("As","Ad"),["Ah","Kd","7c","5s","2c"],91.84),
      ("pair of kings, dry",("Kh","Kd"),["7c","5s","2c","9d","Jh"],45.07),
      ("2-3 offsuit (no pair/draw)",("2c","3d"),["8h","9s","Jd","Qh","Kc"],0.00),
      ("2-7 offsuit (no pair/draw)",("2d","7c"),["8h","9s","Jd","Qh","Kc"],0.00),
      ("2-3 offsuit (all-high board)",("2c","3d"),["Ah","Kd","Qc","Js","9h"],0.02)]
def ids_of(hole,board):
    v=[0]*7
    for i,c in enumerate(list(hole)+list(board)): v[i]=1+4*RANKS.index(c[0])+SUITS.index(c[1])
    return torch.tensor([v],dtype=torch.long)
print(f"\n{'scenario':30} {'MC truth':>9} {'model':>8} {'error':>8}")
errs=[]
with torch.no_grad():
    for name,hole,board,truth in SCEN:
        p=float(net(ids_of(hole,board)))*100; errs.append(abs(p-truth))
        print(f"{name:30} {truth:8.2f}% {p:7.2f}% {p-truth:+7.2f}")
top=[e for (n,h,b,t),e in zip(SCEN,errs) if t>40]; bot=[e for (n,h,b,t),e in zip(SCEN,errs) if t<1]
print(f"\nmean |error| {np.mean(errs):.2f} | truth>40% region {np.mean(top):.2f} | truth<1% region {np.mean(bot):.2f}")
