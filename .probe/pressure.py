"""Under forced postflop pressure: does the trained model fold, and does it ever fold a bad hand?
Pressure is created by seating five copies of the 20%-all-in raiser, so betting happens on every street."""
import collections, numpy as np, torch, torch.nn as nn, engine, agents, evaluation
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
        m=(~pad).unsqueeze(-1).float(); return s.head((x*m).sum(1)/m.sum(1).clamp(min=1.0))
sd=torch.load('.probe/attn60.pt'); remap={'pos.':'posemb.','n1.':'norm.','n2.':'ffn.'}
fixed={}
for k,v in sd.items():
    for a,b in remap.items():
        if k.startswith(a): k=b+k[len(a):]; break
    fixed[k]=v
sup=Attn(); sup.load_state_dict(fixed); sup.eval()
def strength(hole, board):
    v=[0]*7
    for i,c in enumerate(list(hole)+list(board)):
        if i<7: v[i]=1+4*RANKS.index(str(c)[0])+SUITS.index(str(c)[1])
    with torch.no_grad(): return float(sup(torch.tensor([v])))
pol=evaluation.policy_from('.probe/strength-control-s0/strength-control-s0/card-tokens/seed-0/final.ckpt', exploration='off')
import sys
OPP=sys.argv[1] if len(sys.argv)>1 else 'oracle'
aggro=agents.build_baseline(OPP,0) if OPP!='raiser' else evaluation.policy_from('/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt', exploration='off')
faced=collections.Counter(); folded=collections.Counter(); rev=0; hands=0
buckets=collections.defaultdict(lambda:[0,0])
for h in range(1200):
    seat=h%5
    seats=[aggro]*6; seats[seat]=pol
    r=engine.play_hand(9_700_000+h, shape=SH, seats=tuple(seats))
    hands+=1; rev += 1 if r.get('reveal') else 0
    for d in r['decisions']:
        if d['seat'][0]!=seat: continue
        rd=d['readout']; pressure = rd['to_call']>0
        faced[(rd['street'],pressure)]+=1
        if d['action']=='fold': folded[(rd['street'],pressure)]+=1
        if pressure:
            s_=strength(rd['hole'], rd['board'])
            b='weak (<0.10)' if s_<0.10 else 'mid (<0.25)' if s_<0.25 else 'strong (>=0.25)'
            buckets[b][0]+=1
            if d['action']=='fold': buckets[b][1]+=1
print(f"five {OPP} opponents at the table; hands {hands}, reached the reveal {rev} ({100*rev/hands:.1f}%)")
print(f"\n{'street':8} {'facing bet?':12} {'decisions':>10} {'fold %':>8}")
for (st,p),n in sorted(faced.items()):
    print(f"{st:8} {str(p):12} {n:10d} {100*folded[(st,p)]/n:7.1f}%")
print("\nwhen facing a bet, by the supervised model's own strength estimate:")
for b in ('weak (<0.10)','mid (<0.25)','strong (>=0.25)'):
    n,f=buckets[b]; print(f"  {b:16} decisions {n:6d}  fold {100*f/n if n else 0:5.1f}%")
