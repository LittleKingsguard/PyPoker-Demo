"""Train the NAIVE model at six seats: flat-numeric encoding + naive-stack (no embedding, no attention)."""
import copy, os, json, training, agents
SH='six-seat-no-limit-100'
POOL={'game':SH,'members':[],'m':5,'frozen':True,
      'baselines':['fold-no-pair-or-face','fold-no-pair-or-better','fold-large-bet']}
c=copy.deepcopy(training.rung('R3')); c['name']='naive6'; c['game']=SH
for v in c['variants']:
    v['game']=SH
    v['encoding']='flat-numeric'
    v['architecture']={'kind':'naive-stack','width':36,'depth':2}
    v['utility']='net-chips-normalised'
c['pool']=copy.deepcopy(POOL)
os.environ['PYPOKER_CHECKPOINT_ROOT']=os.path.abspath('.probe/naive')
rec=training.run(c, seeds=(0,), budget=5000)
print("checkpoint:", rec['checkpoints']['flat-numeric']['0']['final'])
