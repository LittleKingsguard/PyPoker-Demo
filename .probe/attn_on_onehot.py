"""Same attention architecture, but each slot's input is the 17-dim one-hot (flat encoding) projected
to 50, instead of a learned 50-dim card embedding.  Isolates attention from the embedding."""
import numpy as np, torch, torch.nn as nn, sys
EPOCHS=int(sys.argv[1]) if len(sys.argv)>1 else 200
X=np.load('/tmp/es_X.npy').astype('float32'); Y=np.load('/tmp/es_Y.npy').astype('float32'); S=np.load('/tmp/es_S.npy')
B7=X.reshape(-1,7,17)                       # (N, 7 slots, 17 one-hots)
deal=(B7.max(axis=2)!=0)                    # which slots hold a card
n=len(B7); perm=np.random.default_rng(1).permutation(n); cut=int(n*.85)
Xtr=torch.from_numpy(B7[perm[:cut]]); Dtr=torch.from_numpy(deal[perm[:cut]])
Ytr=torch.from_numpy(Y[perm[:cut]].reshape(-1,1))
Xte=torch.from_numpy(B7[perm[cut:]]); Dte=torch.from_numpy(deal[perm[cut:]])
Yte=torch.from_numpy(Y[perm[cut:]].reshape(-1,1)); Ste=S[perm[cut:]]
POS=torch.arange(7).unsqueeze(0)
class AttnOneHot(nn.Module):
    """17 one-hots -> Linear(17,50) per slot  +  positional  -> attention  -> masked mean -> head."""
    def __init__(s,d=50,h=5,L=2,w=96):
        super().__init__(); s.proj=nn.Linear(17,d); s.posemb=nn.Embedding(7,d)
        s.mha=nn.ModuleList([nn.MultiheadAttention(d,h,batch_first=True) for _ in range(L)])
        s.norm=nn.ModuleList([nn.LayerNorm(d) for _ in range(L)]); s.ffn=nn.ModuleList([nn.LayerNorm(d) for _ in range(L)])
        s.ff=nn.ModuleList([nn.Sequential(nn.Linear(d,w),nn.ReLU(),nn.Linear(w,d)) for _ in range(L)])
        s.head=nn.Sequential(nn.Linear(d,w),nn.ReLU(),nn.Linear(w,w),nn.ReLU(),nn.Linear(w,1),nn.Sigmoid())
    def forward(s, x, present):
        pad=~present; h=s.proj(x)+s.posemb(POS[:, :x.shape[1]])
        for m,a,f,b in zip(s.mha,s.norm,s.ff,s.ffn):
            y,_=m(h,h,h,key_padding_mask=pad,need_weights=False); h=a(h+y); h=b(h+f(h))
        m=(~pad).unsqueeze(-1).float(); return s.head((h*m).sum(1)/m.sum(1).clamp(min=1.0))
torch.manual_seed(0); net=AttnOneHot()
print("attention on the flat one-hot: params", sum(p.numel() for p in net.parameters()), flush=True)
opt=torch.optim.Adam(net.parameters(),1e-3); lossf=nn.BCELoss(); B=4096
for ep in range(1,EPOCHS+1):
    p=torch.randperm(len(Xtr))
    for i in range(0,len(Xtr),B):
        b=p[i:i+B]; opt.zero_grad(); lossf(net(Xtr[b],Dtr[b]),Ytr[b]).backward(); opt.step()
    if ep%20==0:
        with torch.no_grad():
            pred=net(Xte,Dte); per={}
            for st in (3,4,5):
                m=(Ste==st); per[st]=100*(1-float(((pred[m]-Yte[m])**2).mean())/float(((Yte[m]-Yte[m].mean())**2).mean()))
            tot=100*(1-float(((pred-Yte)**2).mean())/float(((Yte-Yte.mean())**2).mean()))
        print(f"  epoch {ep:3d}: overall {tot:5.2f}%   flop {per[3]:5.2f}%  turn {per[4]:5.2f}%  river {per[5]:5.2f}%", flush=True)
        torch.save(net.state_dict(), '/media/ryanr/Shared Files/Projects/PyPoker-Demo/.probe/attn_onehot.pt')
