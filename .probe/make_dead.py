"""Train a net-chips (600-scale) six-seat token learner so the dead trunk can be drawn from a real artefact."""
import copy, os, sys, training
SH='six-seat-no-limit-100'
POOL={'game':SH,'members':[],'m':5,'frozen':True,
      'baselines':['fold-no-pair-or-face','fold-no-pair-or-better','fold-large-bet']}
c=copy.deepcopy(training.rung('R3')); c['name']='dead-ckpt'; c['game']=SH
for v in c['variants']: v['game']=SH; v['utility']='net-chips'
c['pool']=copy.deepcopy(POOL)
os.environ['PYPOKER_CHECKPOINT_ROOT']=os.path.abspath('.probe/dead')
rec=training.run(c, seeds=(0,), budget=3000)
print("checkpoint:", rec['checkpoints']['card-tokens']['0']['final'])
