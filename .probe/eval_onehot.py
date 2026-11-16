import numpy as np, torch, torch.nn as nn
X=np.load('/tmp/es_X.npy').astype('float32'); Y=np.load('/tmp/es_Y.npy').astype('float32'); S=np.load('/tmp/es_S.npy')
B7=X.reshape(-1,7,17); deal=(B7.max(axis=2)!=0)
perm=np.random.default_rng(1).permutation(len(B7)); cut=int(len(B7)*.85)
Xte=torch.from_numpy(B7[perm[cut:]]); Dte=torch.from_numpy(deal[perm[cut:]])
Yte=torch.from_numpy(Y[perm[cut:]].reshape(-1,1)); Ste=S[perm[cut:]]
POS=torch.arange(7).unsqueeze(0)
class M(nn.Module):
    def __init__(s,d=50,h=5,L=2,w=96):
        super().__init__(); s.proj=nn.Linear(17,d); s.posemb=nn.Embedding(7,d)
        s.mha=nn.ModuleList([nn.MultiheadAttention(d,h,batch_first=True) for _ in range(L)])
        s.norm=nn.ModuleList([nn.LayerNorm(d) for _ in range(L)]); s.ffn=nn.ModuleList([nn.LayerNorm(d) for _ in range(L)])
        s.ff=nn.ModuleList([nn.Sequential(nn.Linear(d,w),nn.ReLU(),nn.Linear(w,d)) for _ in range(L)])
        s.head=nn.Sequential(nn.Linear(d,w),nn.ReLU(),nn.Linear(w,w),nn.ReLU(),nn.Linear(w,1),nn.Sigmoid())
    def forward(s,x,present):
        pad=~present; h=s.proj(x)+s.posemb(POS[:, :x.shape[1]])
        for m,a,f,b in zip(s.mha,s.norm,s.ff,s.ffn):
            y,_=m(h,h,h,key_padding_mask=pad,need_weights=False); h=a(h+y); h=b(h+f(h))
        m=(~pad).unsqueeze(-1).float(); return s.head((h*m).sum(1)/m.sum(1).clamp(min=1.0))
net=M(); net.load_state_dict(torch.load('.probe/attn_onehot.pt')); net.eval()
with torch.no_grad():
    pred=net(Xte,Dte)
    tot=100*(1-float(((pred-Yte)**2).mean())/float(((Yte-Yte.mean())**2).mean()))
    per={}
    for st in (3,4,5):
        m=(Ste==st); per[st]=100*(1-float(((pred[m]-Yte[m])**2).mean())/float(((Yte[m]-Yte[m].mean())**2).mean()))
print(f"attention on ONE-HOT (current checkpoint): overall {tot:.2f}%   flop {per[3]:.2f}%  turn {per[4]:.2f}%  river {per[5]:.2f}%")
print("for reference, token+attention: 25.1% at ep20, 28.1% at ep60, 32.4% at ep120, 34.1% at ep200, 40.0% at ep400")
