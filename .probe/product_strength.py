"""The product's own learner with the strength input and the seeded embeddings, against the league.
Arms: 'strength' (strength=supervised + embedding_init from attn-60) and 'control' (neither)."""
import copy, os, sys, json, collections, numpy as np, training, agents, evaluation, engine
ARM=sys.argv[1]; SEED=int(sys.argv[2]); BUDGET=int(sys.argv[3]); EVAL=2000
SH='six-seat-no-limit-100'
LEAGUE=['/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt',
        '/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt',
        '/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt']
import zipfile
def records(path):
    with zipfile.ZipFile(path) as z:
        d=json.loads(z.read([n for n in z.namelist() if n.endswith('.json')][0]))
    return d.get('utility') or d.get('variant',{}).get('utility'), d.get('rule') or d.get('variant',{}).get('rule','masked-q-learning')
members=[]
for i,p in enumerate(LEAGUE):
    util, rule = records(p)
    members.append({'id':f'league-{i}','path':p,'rung':'R3','variant':'league','seed':0,'step':1000,
                    'samples':1000,'lineage':'league','rule':rule or 'masked-q-learning','utility':util,'game':SH})
POOL={'game':SH,'members':members,'m':5,'frozen':True,'baselines':['fold-no-pair-or-face','fold-no-pair-or-better','fold-large-bet']}
c=copy.deepcopy(training.rung('R3')); c['name']=f'strength-{ARM}-s{SEED}'; c['game']=SH
for v in c['variants']:
    v['game']=SH; v['utility']='stack-shortfall'
    if ARM=='strength':
        v['strength']='supervised'; v['strength_source']='attn-60'
        v['embedding_init']={'source':'attn-60','rows':'cards'}
c['pool']=copy.deepcopy(POOL)
os.environ['PYPOKER_CHECKPOINT_ROOT']=os.path.abspath(f'.probe/strength-{ARM}-s{SEED}')
rec=training.run(c, seeds=(SEED,), budget=BUDGET)
final=rec['checkpoints']['card-tokens'][str(SEED)]['final']
# evaluate the trained policy on 2,000 hands against the same league
pol=evaluation.policy_from(final, exploration='off')
leaguers=[evaluation.policy_from(p, exploration='off') for p in LEAGUE]
caller=agents.build_baseline('always-call',0)
chips=[]; census=collections.Counter()
for h in range(EVAL):
    seat=h%5
    seats=[leaguers[(s+seat)%3] if (s+seat)%5 else caller for s in range(6)]
    seats[seat]=pol
    res=engine.play_hand(7_000_000+SEED*100_000+h, shape=SH, seats=tuple(seats))
    chips.append(res['payoffs'][seat])
    for d in res['decisions']:
        if d['seat'][0]==seat: census[d['action']]+=1
m=float(np.mean(chips)); ci=2*float(np.std(chips))/len(chips)**0.5
tot=sum(census.values()) or 1
print(json.dumps({'arm':ARM,'seed':SEED,'budget':BUDGET,'format':rec['checkpoints'].get('format_version'),
                  'chips':round(m,3),'ci':round(ci,3),
                  'census':{k:round(100*v/tot,1) for k,v in census.most_common()}}))
