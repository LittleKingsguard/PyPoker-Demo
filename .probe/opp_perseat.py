"""Per-seat opponent model: history FILTERED to the acting seat, optionally identity-conditioned.
Reports the training set's class bias alongside per-opponent balanced accuracy and per-class recall."""
import sys, random, json, collections, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
import engine, agents, evaluation
SEATS=6; SH='six-seat-no-limit-100'; MAXT=32
VERBS={'fold':0,'check':1,'call':1,'bet':2,'raise':2}
STREETS={'preflop':0,'flop':1,'turn':2,'river':3}
ACT3={'fold':0,'check-call':1,'raise-minimum':2,'raise-quarter':2,'raise-half':2,'raise-all-in':2}
OPPS=[('folder','/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt'),
      ('raiser-50-50','/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt'),
      ('raiser-83','/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt'),
      ('fold-no-pair-or-face',None)]
def policy_of(name,path):
    return evaluation.policy_from(path, exploration='off') if path else agents.build_baseline(name,0)
def tok_seat(history, seat):
    """Only the entries belonging to `seat`: 4 tokens each (street, verb, amount, action index)."""
    ids=[]
    for i,e in enumerate(history):
        p=e.split()
        if len(p)<4 or int(p[2])!=seat: continue
        ids += [1+STREETS.get(p[0],0), 5+VERBS.get(p[3],1),
                9+(0 if len(p)<=4 or not p[4].isdigit() else min(3,1+int(np.log2(int(p[4]))))), 13+min(3,i%4)]
    return ids[-MAXT:]
def pub(rd, ident=None):
    v=[rd['pot']/600.0, rd['to_call']/100.0, STREETS[rd['street']]/3.0, len(rd['board'])/5.0,
       rd['stacks'][rd['seat'][0]]/100.0]
    v += [1.0 if ident==k else 0.0 for k in range(len(OPPS))]
    return v
class Net(nn.Module):
    def __init__(s,d=32,h=4,w=64):
        super().__init__(); s.emb=nn.Embedding(24,d); s.pos=nn.Embedding(MAXT,d)
        s.att=nn.MultiheadAttention(d,h,batch_first=True); s.n1=nn.LayerNorm(d)
        s.ff=nn.Sequential(nn.Linear(d,w),nn.ReLU(),nn.Linear(w,d)); s.n2=nn.LayerNorm(d)
        s.pub=nn.Linear(5+len(OPPS),d); s.act=nn.Linear(d,3)
    def forward(s,tok,p):
        pad=tok==0; x=s.emb(tok)+s.pos(torch.arange(tok.shape[1]).unsqueeze(0))
        a,_=s.att(x,x,x,key_padding_mask=pad,need_weights=False); x=s.n1(x+a); x=s.n2(x+s.ff(x))
        m=(~pad).unsqueeze(-1).float(); h=(x*m).sum(1)/m.sum(1).clamp(min=1.0)
        return s.act(h+s.pub(p))
def collect(n_hands, seed, with_ident):
    rows=[]
    for h in range(n_hands):
        k=h%len(OPPS); name,path=OPPS[k]
        pol=policy_of(name,path)
        r=engine.play_hand(seed*100_000+h, shape=SH, seats=(pol,)*6)
        for d in r['decisions']:
            seat=d['seat'][0]; rd=d['readout']
            rows.append({'tok':tok_seat(rd['history'], seat), 'pub':pub(rd, k if with_ident else None),
                         'y':ACT3.get(d['action'],1), 'opp':name})
    return rows
def train_eval(rows, tag):
    tok=torch.tensor([r['tok']+[0]*(MAXT-len(r['tok'])) for r in rows])
    p=torch.tensor([r['pub'] for r in rows], dtype=torch.float32)
    y=torch.tensor([r['y'] for r in rows]); opp=np.array([r['opp'] for r in rows])
    n=len(rows); perm=np.random.default_rng(1).permutation(n); cut=int(n*.8)
    tr,te=perm[:cut],perm[cut:]
    torch.manual_seed(0); net=Net(); opt=torch.optim.Adam(net.parameters(),2e-3)
    cnt=torch.bincount(y[tr],minlength=3).float(); w=(cnt.sum()/(3*cnt)).clamp(max=10)
    for ep in range(10):
        q=torch.randperm(len(tr))
        for i in range(0,len(tr),1024):
            b=tr[q[i:i+1024]]; loss=F.cross_entropy(net(tok[b],p[b]),y[b],weight=w)
            opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad(): pred=net(tok[te],p[te]).argmax(1).numpy()
    a=y[te].numpy(); o=opp[te]
    print(f"\n[{tag}] train class mix (fold/call/raise): " +
          "/".join(f"{100*v/len(tr):.1f}" for v in torch.bincount(y[tr],minlength=3).tolist()))
    print(f"  held-out rows {len(a)} | accuracy {np.mean(pred==a):.3f} | balanced accuracy {np.mean([np.mean(pred[a==c]==c) for c in (0,1,2)]):.3f}")
    for name,_ in OPPS:
        m=o==name
        if m.sum()==0: continue
        aa,pp=a[m],pred[m]; maj=np.bincount(aa,minlength=3).argmax()
        rec={c:(np.mean(pp[aa==c]==c) if (aa==c).sum() else float('nan')) for c in (0,1,2)}
        print(f"   {name:22} n={m.sum():5d} actual {'/'.join(f'{100*np.mean(aa==c):.0f}' for c in (0,1,2)):>11}"
              f"  pred {'/'.join(f'{100*np.mean(pp==c):.0f}' for c in (0,1,2)):>11}"
              f"  acc {np.mean(pp==aa):.3f} base {np.mean(aa==maj):.3f}"
              f"  rec F/C/R {rec[0]:.2f}/{rec[1]:.2f}/{rec[2]:.2f}")
    return
rows_noid=collect(400, 21, False)
train_eval(rows_noid, "per-seat history, NO identity")
rows_id=collect(400, 21, True)
train_eval(rows_id, "per-seat history + identity")
# ---- freeze the per-seat, identity-conditioned model for the policy integration ----
import torch as _t
tok=_t.tensor([r['tok']+[0]*(MAXT-len(r['tok'])) for r in rows_id])
pp=_t.tensor([r['pub'] for r in rows_id], dtype=_t.float32)
yy=_t.tensor([r['y'] for r in rows_id])
_t.manual_seed(0); net=Net(); opt=_t.optim.Adam(net.parameters(),2e-3)
cnt=_t.bincount(yy,minlength=3).float(); w=(cnt.sum()/(3*cnt)).clamp(max=10)
for ep in range(12):
    q=_t.randperm(len(tok))
    for i in range(0,len(tok),1024):
        b=q[i:i+1024]; loss=_t.nn.functional.cross_entropy(net(tok[b],pp[b]),yy[b],weight=w)
        opt.zero_grad(); loss.backward(); opt.step()
_t.save(net.state_dict(), '.probe/opp_seat.pt')
print("frozen per-seat artefact: .probe/opp_seat.pt")
