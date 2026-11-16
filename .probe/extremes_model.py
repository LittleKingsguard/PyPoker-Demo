import random, numpy as np, pokerkit as pk, torch, torch.nn as nn
RANKS='23456789TJQKA'; SUITS='cdhs'; DECK=[r+s for r in RANKS for s in SUITS]
CARD={c: list(pk.Card.parse(c))[0] for c in DECK}
SCEN = [
 ("BEST trip aces, no flush/straight", ("As","Ad"), ["Ah","Kd","7c","5s","2c"], 91.84),
 ("BEST quad aces",                    ("As","Ad"), ["Ah","Ac","7d","5s","2h"], 100.00),
 ("BEST nut flush",                    ("As","Qs"), ["Js","9s","4s","2h","7d"], 100.00),
 ("BEST ace-high straight",            ("As","Kd"), ["Qc","Js","Th","2d","7c"], 97.77),
 ("MID  pair of kings, dry",           ("Kh","Kd"), ["7c","5s","2c","9d","Jh"], 45.07),
 ("WORST 2-3 offsuit, no pair/draw",   ("2c","3d"), ["8h","9s","Jd","Qh","Kc"], 0.00),
 ("WORST 2-7 offsuit, no pair/draw",   ("2d","7c"), ["8h","9s","Jd","Qh","Kc"], 0.00),
 ("WORST 2-3 offsuit, all-high board", ("2c","3d"), ["Ah","Kd","Qc","Js","9h"], 0.02),
]
# ---- train the attention card model on the three-street data (as D-88/D-90) ----
X=np.load('/tmp/es_X.npy'); Y=np.load('/tmp/es_Y.npy').astype('float32')
B7=X.reshape(-1,7,17); zero=B7.max(axis=2)==0
r=B7[:,:,:13].argmax(axis=2); s=B7[:,:,13:].argmax(axis=2)
Ids=(1+4*r+s).astype(np.int64); Ids[zero]=0
perm=np.random.default_rng(1).permutation(len(Ids)); cut=int(len(Ids)*.85)
Itr=torch.from_numpy(Ids[perm[:cut]]); Ytr=torch.from_numpy(Y[perm[:cut]].reshape(-1,1))
POS=torch.arange(7).unsqueeze(0)
class Attn(nn.Module):
    def __init__(s,d=50,h=5,L=2,w=96):
        super().__init__(); s.emb=nn.Embedding(53,d); s.pos=nn.Embedding(7,d)
        s.mha=nn.ModuleList([nn.MultiheadAttention(d,h,batch_first=True) for _ in range(L)])
        s.n1=nn.ModuleList([nn.LayerNorm(d) for _ in range(L)]); s.n2=nn.ModuleList([nn.LayerNorm(d) for _ in range(L)])
        s.ff=nn.ModuleList([nn.Sequential(nn.Linear(d,w),nn.ReLU(),nn.Linear(w,d)) for _ in range(L)])
        s.head=nn.Sequential(nn.Linear(d,w),nn.ReLU(),nn.Linear(w,w),nn.ReLU(),nn.Linear(w,1),nn.Sigmoid())
    def forward(s,ids):
        pad=ids==0; x=s.emb(ids)+s.pos(POS[:, :ids.shape[1]])
        for m,n1,ff,n2 in zip(s.mha,s.n1,s.ff,s.n2):
            a,_=m(x,x,x,key_padding_mask=pad,need_weights=False); x=n1(x+a); x=n2(x+ff(x))
        m=(~pad).unsqueeze(-1).float(); return s.head((x*m).sum(1)/m.sum(1).clamp(min=1.0))
torch.manual_seed(0); net=Attn(); opt=torch.optim.Adam(net.parameters(),1e-3); lossf=nn.BCELoss(); B=4096
print("training the attention card model (60 epochs) ...", flush=True)
for ep in range(1,61):
    p=torch.randperm(len(Itr))
    for i in range(0,len(Itr),B):
        b=p[i:i+B]; opt.zero_grad(); lossf(net(Itr[b]),Ytr[b]).backward(); opt.step()
torch.save(net.state_dict(), '.probe/attn60.pt')
def ids_of(hole, board):
    v=[0]*7
    for i,c in enumerate(list(hole)+list(board)):
        v[i]=1+4*RANKS.index(c[0])+SUITS.index(c[1])
    return torch.tensor([v], dtype=torch.long)
print(f"\n{'scenario':36} {'MC truth':>9} {'model':>8} {'error':>8}")
errs=[]
with torch.no_grad():
    for name,hole,board,truth in SCEN:
        p=float(net(ids_of(hole,board)))*100
        errs.append(abs(p-truth))
        print(f"{name:36} {truth:8.2f}% {p:7.2f}% {p-truth:+7.2f}")
print(f"\nmean |error| {np.mean(errs):.2f} points   worst {max(errs):.2f}")
print("ordering correct:", all(SCEN[i][3] >= SCEN[i+1][3] for i in range(len(SCEN)-1)))
