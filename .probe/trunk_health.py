"""Dead-trunk check (the D-60 instrument): active hidden units and weight norms for a checkpoint."""
import numpy as np, sys, agents, engine, evaluation, features
def arr(v):
    try: v=v.detach().cpu().numpy()
    except Exception: pass
    return np.asarray(v, dtype='float64')
def health(path, label):
    pol=evaluation.policy_from(path, exploration='off')
    inner=getattr(pol,'policy',pol)
    if callable(inner) and not hasattr(inner,'_layout'):
        inner=getattr(pol,'member_policy',inner)
    L=inner._layout; p=inner._state.params
    if L.trunk_w is None: print(f"{label}: no trunk"); return
    table = arr(p[L.w_in[0]:L.w_in[0]+L.w_in[1]]).reshape(L.input_dim, L.width)
    W1 = arr(p[L.trunk_w[0][0]:L.trunk_w[0][0]+L.trunk_w[0][1]]).reshape(L.width, L.width)
    b1 = arr(p[L.trunk_b[0]:L.trunk_b[0]+L.width])
    W2 = arr(p[L.trunk_w[1][0]:L.trunk_w[1][0]+L.trunk_w[1][1]]).reshape(L.width, L.width)
    b2 = arr(p[L.trunk_b[1]:L.trunk_b[1]+L.width])
    enc = features.build_encoder('card-tokens', shape='six-seat-no-limit-100',
                                 strength='supervised' if L.input_dim==104 else None)
    f=agents.build_baseline('always-call',0)
    P=[]; Q=[]
    for h in range(300):
        try: r=engine.play_hand(10_000_000+h, shape='six-seat-no-limit-100', seats=(f,f,f,f,f,f))
        except Exception: continue
        d=r['decisions'][0]; rd=d['readout']
        if L.input_dim==104:      # a strength-declaring learner needs the injected key
            rd=dict(rd); rd['strength']=0.17
        ids=np.asarray(features.encode(enc, rd), dtype=np.int64).ravel()
        pooled=((1.0+np.tanh(table[ids]))/2.0).mean(axis=0)
        a1=np.clip(pooled@W1+b1, 0, None)          # ReLU
        Q.append(np.clip(a1@W2+b2, 0, None))
        P.append(a1)
    P=np.asarray(P); Q=np.asarray(Q)
    a1_units=(P>0).mean(axis=0); a2_units=(Q>0).mean(axis=0)
    print(f"{label:44} obs {len(P):4d} | layer1 alive {int((a1_units>0).sum()):2d}/50  layer2 alive {int((a2_units>0).sum()):2d}/50"
          f" | |W1| {np.linalg.norm(W1):7.2f} |W2| {np.linalg.norm(W2):7.2f}"
          f" | distinct layer1 activations {len(np.unique(P.round(9),axis=0)):4d}")
if __name__=='__main__':
    for path,label in (('.probe/strength-control-s0/strength-control-s0/card-tokens/seed-0/final.ckpt','15k net-chips, control (ours)'),
                       ('.probe/strength-strength-s0/strength-strength-s0/card-tokens/seed-0/final.ckpt','15k net-chips, strength+seeded'),
                       ('/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt','foldloop-high, net-chips-normalised'),
                       ('/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt','foldloop-control, net-chips-normalised'),
                       ('/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt','raiser-seed, net-chips')):
        try: health(path,label)
        except Exception as e: print(f"{label:44} failed {type(e).__name__} {str(e)[:60]}")
