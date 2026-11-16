"""Measure the effect of copying supervised card embeddings into a policy learner's token table,
by scoring the loaded-deal suite before and after the copy (in memory, no checkpoint rewrite)."""
import glob, os, numpy as np, torch, torch.nn as nn, agents, evaluation, engine
SRC='.probe/attn60.pt'; SH='six-seat-no-limit-100'
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
        for m,a,f,b in zip(s.mha,s.n1,s.ff,s.n2):
            y,_=m(x,x,x,key_padding_mask=pad,need_weights=False); x=a(x+y); x=b(x+f(x))
        m=(~pad).unsqueeze(-1).float(); return s.head((x*m).sum(1)/m.sum(1).clamp(min=1.0))
sup=Attn(); sup.load_state_dict(torch.load(SRC)); card_rows=sup.emb.weight.detach()[1:53].clone()
final=sorted(glob.glob('.probe/ckpt/**/final.ckpt', recursive=True))[0]
pol=evaluation.policy_from(final, exploration='off')
inner=pol.policy; L=inner._layout; p=inner._state.params
print("policy:", final.split('/')[-3:], "| embedding block", L.w_in, "| input_dim", L.input_dim)
f1=agents.build_baseline('fold-no-pair-or-face',0); f2=agents.build_baseline('fold-no-pair-or-better',0)
caller=agents.build_baseline('always-call',0)
DRY=["3s","6d","9d","4c","Jh"]; FILL=[("3c","4d"),("Jc","Td"),("3h","5h"),("4s","6c"),("5d","6s")]
def deal(hole, seat=3):
    holes=[]; k=0
    for s in range(6):
        if s==seat: holes.append(list(hole))
        else: holes.append(list(FILL[k])); k+=1
    return {"holes":holes,"board":list(DRY)}
HOLES=[("AA",("As","Ad")),("KQs",("Ks","Qs")),("22",("2s","2h")),("87s",("8s","7s")),("72o",("7c","2d"))]
def score(tag):
    out={}
    for name,hole in HOLES:
        r=engine.play_hand(20261115, shape=SH, seats=(f1,caller,f2,pol,f1,f2), deal=deal(hole))
        out[name]=[d['action'] for d in r['decisions'] if d['seat'][0]==3][:2]
    distinct=len({tuple(v) for v in out.values()})
    print(f"  {tag:22} distinct {distinct}/5   " + "  ".join(f"{k}={'/'.join(v)}" for k,v in out.items()))
    return distinct
d0=score("baseline embeddings")
blk=p[L.w_in[0]:L.w_in[0]+L.w_in[1]].reshape(L.input_dim, L.width)
arr=blk.detach().cpu().numpy().copy()
arr[1:53,:50]=card_rows.numpy()                                   # the 52 card ids, 50 dims each
with torch.no_grad(): blk.copy_(torch.from_numpy(arr).to(blk.dtype))
d1=score("supervised embeddings")
print(f"\ncard-dependence: baseline {d0}/5 -> copied {d1}/5")
