"""Measure each model group the UI offers, against one fixed opponent set, so the drawer can sort by
performance.  Six-seat groups play five copies of the league mix; the fixed-limit group plays its own
two-seat shape against always-call, because it cannot sit at a six-seat table."""
import json, collections, numpy as np, engine, agents, evaluation, sys
sys.path.insert(0, 'ui')
import table as T

SH6 = 'six-seat-no-limit-100'
LEAGUE = ['/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt',
          '/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt',
          '/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt']
mix = [evaluation.policy_from(p, exploration='off') for p in LEAGUE]
caller = agents.build_baseline('always-call', 0)
HANDS = 400

GROUPS = {
    'Naive · flat numbers': ('checkpoints/R1/naive-numeric/seed-0/final.ckpt', 'two-seat'),
    'Naive, six seats · flat numbers': ('.probe/naive/naive6/card-tokens/seed-0/final.ckpt', 'six-seat'),
    'Dead trunk · 600-scale reward': ('.probe/dead/dead-ckpt/card-tokens/seed-0/final.ckpt', 'six-seat'),
    'Live trunk, masked pooler · seed 0': ('.probe/strength-control-s0/strength-control-s0/card-tokens/seed-0/final.ckpt', 'six-seat'),
    'Live trunk, masked pooler · seed 1': ('.probe/strength-control-s1/strength-control-s1/card-tokens/seed-1/final.ckpt', 'six-seat'),
    'Live trunk, masked pooler · seed 2': ('.probe/strength-control-s2/strength-control-s2/card-tokens/seed-2/final.ckpt', 'six-seat'),
    'Live trunk + card strength · seed 0': ('.probe/strength-strength-s0/strength-strength-s0/card-tokens/seed-0/final.ckpt', 'six-seat'),
    'Live trunk + card strength · seed 1': ('.probe/strength-strength-s1/strength-strength-s1/card-tokens/seed-1/final.ckpt', 'six-seat'),
    'Live trunk + card strength · seed 2': ('.probe/strength-strength-s2/strength-strength-s2/card-tokens/seed-2/final.ckpt', 'six-seat'),
    'Seeded card embeddings · probe': ('.probe/ckpt/wire-sup-emb/card-tokens/seed-0/final.ckpt', 'six-seat'),
}
out = {}
for group, (path, kind) in GROUPS.items():
    try:
        pol = evaluation.policy_from(path, exploration='off')
    except Exception as error:
        out[group] = {'chips': None, 'ci': None, 'note': 'unreadable: %s' % error, 'hands': 0}
        print(f'{group:42} unreadable {type(error).__name__}')
        continue
    chips = []
    try:
        if kind == 'six-seat':
            for h in range(HANDS):
                seat = h % 5
                seats = [mix[(s + seat) % 3] if (s + seat) % 5 else caller for s in range(6)]
                seats[seat] = pol
                chips.append(engine.play_hand(41_000_000 + h, shape=SH6, seats=tuple(seats))['payoffs'][seat])
            note = 'six-seat, vs the league mix'
        else:
            for h in range(HANDS):
                chips.append(engine.play_hand(42_000_000 + h, shape='fixed-limit-20',
                                              seats=(pol, caller))['payoffs'][0])
            note = 'two-seat fixed-limit, vs always-call'
    except Exception as error:
        out[group] = {'chips': None, 'ci': None, 'note': 'failed: %s' % error, 'hands': 0}
        print(f'{group:42} failed {type(error).__name__}: {error}')
        continue
    m = float(np.mean(chips)); ci = 2 * float(np.std(chips)) / len(chips) ** 0.5
    out[group] = {'chips': round(m, 3), 'ci': round(ci, 3), 'hands': HANDS, 'note': note}
    print(f'{group:42} {m:+7.3f} +-{ci:5.2f}   ({note})')

# the two saved probe heads: the best-measured arms (3 seeds each, D-126)
out['Top performer · exploration floor 0.60'] = {'chips': 11.30, 'ci': 4.16, 'hands': 6000,
    'note': 'six-seat, vs the league mix; 3 seeds (D-126)'}
out['Top performer · floor 0.60 + opponent model'] = {'chips': 12.92, 'ci': 5.28, 'hands': 6000,
    'note': 'six-seat, vs the league mix; 3 seeds (D-126)'}
json.dump(out, open('ui/performance.json', 'w'), indent=1, sort_keys=True)
print('\nwrote ui/performance.json with', len(out), 'groups')
