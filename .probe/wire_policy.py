"""Probe: train the product's token policy learner, copy the supervised card embeddings in, and
measure both on the loaded-deal suite.  The supervised model supplies the embedding rows for ids 1..52."""
import copy, os, sys, collections, numpy, torch, torch.nn as nn, training, agents, evaluation, engine
SRC = sys.argv[1] if len(sys.argv) > 1 else '.probe/attn60.pt'
SH='six-seat-no-limit-100'
# --- the supervised attention model, for its card embedding -------------------------------------
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
sup=Attn(); sup.load_state_dict(torch.load(SRC)); sup.eval()
card_rows = sup.emb.weight.detach()[1:53].clone()          # ids 1..52 = the 52 cards
print("supervised embeddings:", tuple(card_rows.shape), "from", SRC)
# --- the product's token policy learner, six seats ---------------------------------------------
POOL = {'game':SH,'members':[],'m':5,'frozen':True,
        'baselines':['fold-no-pair-or-face','fold-no-pair-or-better','fold-large-bet']}
c = copy.deepcopy(training.rung('R3')); c['name']='wire-sup-emb'; c['game']=SH
for v in c['variants']:
    v['game']=SH; v['utility']='stack-shortfall'
c['pool']=copy.deepcopy(POOL)
os.environ['PYPOKER_CHECKPOINT_ROOT']=os.path.abspath('.probe/ckpt')
import glob
existing = sorted(glob.glob(os.path.abspath('.probe/ckpt') + '/**/final.ckpt', recursive=True))
if existing:
    final = existing[0]; print("reusing trained policy learner:", final)
else:
    rec = training.run(c, seeds=(0,), budget=5000)
    final = rec['checkpoints']['card-tokens']['0']['final']
inner = evaluation.policy_from(final, exploration='off').policy
L = inner._layout; p = inner._state.params
print("policy layout: input_dim", L.input_dim, "width", L.width, "(embedding block", L.w_in, ")")
# copy the supervised rows into the policy's embedding for the 52 card ids
before = p[L.w_in[0]:L.w_in[0]+L.w_in[1]].reshape(L.input_dim, L.width).clone()
block = p[L.w_in[0]:L.w_in[0]+L.w_in[1]].reshape(L.input_dim, L.width)
import numpy as np
blk = np.asarray(block.detach().cpu().numpy() if hasattr(block,'detach') else block, dtype='float64')
blk[1:53, :50] = card_rows.numpy()
if hasattr(block,'detach'):
    with torch.no_grad(): block.copy_(torch.from_numpy(blk).to(block.dtype))
else:
    block[:] = blk
patched_path = os.path.abspath('.probe/patched.ckpt')
inner._backend.load_state  # keep the API surface
agents.save(inner, patched_path) if hasattr(agents,'save') else None
print("patched embedding rows 1..52 from the supervised model; wrote", patched_path)
