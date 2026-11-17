"""Node-link diagram of the token learner's trunk: DEAD (600-scale reward) vs LIVE (normalised).
Reads the checkpoints' parameters directly and measures per-unit activity on real observations.
Hollow rings = units that never fire; lit nodes = units that fire; edges = the strongest weights
between units that actually fire."""
import json, zipfile, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle
import engine, agents, features
plt.rcParams.update({'svg.fonttype':'none','axes.facecolor':'none','figure.facecolor':'none',
                     'savefig.facecolor':'none','text.color':'#f2e8d5','font.size':9})
GOLD,LIT,DARK,RING='#d9a441','#f2e8d5','#241f1a','#6b6255'
SH='six-seat-no-limit-100'; VOCAB=102; W=50; H=50; ACT=6
OFF={'w_in':(0,VOCAB*W),'w1':(VOCAB*W,W*H),'b1':(VOCAB*W+W*H,H),
     'w2':(VOCAB*W+W*H+H,H*H),'b2':(VOCAB*W+W*H+H+H*H,H),
     'wo':(VOCAB*W+W*H+H+H*H+H,H*ACT),'bo':(VOCAB*W+W*H+H+H*H+H+H*ACT,ACT)}
def load(path):
    with zipfile.ZipFile(path) as z:
        p=np.load(z.open('parameters.npy'))
    g=lambda k,n: p[OFF[k][0]:OFF[k][0]+OFF[k][1]].reshape(n)
    return {'tab':g('w_in',(VOCAB,W)),'W1':g('w1',(W,H)),'b1':p[OFF['b1'][0]:OFF['b1'][0]+H],
            'W2':g('w2',(H,H)),'b2':p[OFF['b2'][0]:OFF['b2'][0]+H],'Wo':g('wo',(H,ACT))}
def activity(m, n_obs=300):
    enc=features.build_encoder('card-tokens', shape=SH)
    f=agents.build_baseline('always-call',0); A1=[]; A2=[]; P=[]
    for h in range(n_obs):
        r=engine.play_hand(20_000_000+h, shape=SH, seats=(f,)*6)
        ids=np.asarray(features.encode(enc, r['decisions'][0]['readout']), dtype=np.int64).ravel()
        rows=(1.0+np.tanh(m['tab'][ids]))/2.0
        real=ids!=0
        pooled=rows[real].sum(0)/max(1,real.sum())
        a1=np.clip(pooled@m['W1']+m['b1'],0,None); a2=np.clip(a1@m['W2']+m['b2'],0,None)
        A1.append(a1); A2.append(a2); P.append(pooled)
    A1,A2,P=np.asarray(A1),np.asarray(A2),np.asarray(P)
    return P,A1,A2
def draw(ax, m, path_label, title, topk=46):
    P,A1,A2=activity(m)
    f1=(A1>0).mean(0); f2=(A2>0).mean(0)
    alive1=int((f1>0).sum()); alive2=int((f2>0).sum())
    cols=[P.mean(0), A1.mean(0), A2.mean(0), None]
    xs=[0,1.05,2.1,3.15]
    def ys(n): return np.linspace(0,1,n)
    # pool: the 20 strongest input dims
    pool_idx=np.argsort(-np.linalg.norm(m['W1'],axis=1))[:20]
    pos=[{} for _ in range(4)]
    for k,i in enumerate(pool_idx): pos[0][i]=(xs[0],ys(20)[k])
    for i in range(H): pos[1][i]=(xs[1],ys(H)[i])
    for i in range(H): pos[2][i]=(xs[2],ys(H)[i])
    for i in range(ACT): pos[3][i]=(xs[3],ys(ACT)[i])
    # edges: strongest weights between units that FIRE
    segs=[]; vals=[]
    for i in pool_idx:
        for j in np.argsort(-np.abs(m['W1'][i]))[:3]:
            if f1[j]>0: segs.append([pos[0][i],pos[1][int(j)]]); vals.append(abs(m['W1'][i][j]))
    for i in range(H):
        if f1[i]<=0: continue
        for j in np.argsort(-np.abs(m['W2'][i]))[:2]:
            if f2[int(j)]>0: segs.append([pos[1][i],pos[2][int(j)]]); vals.append(abs(m['W2'][i][j]))
    for i in range(H):
        if f2[i]<=0: continue
        for j in range(ACT):
            if abs(m['Wo'][i][j])>np.percentile(np.abs(m['Wo']),85):
                segs.append([pos[2][i],pos[3][j]]); vals.append(abs(m['Wo'][i][j]))
    if segs:
        v=np.asarray(vals); a=0.12+0.75*(v-v.min())/(np.ptp(v)+1e-9)
        lc=LineCollection(segs, colors=[(0.85,0.80,0.70,float(al)) for al in a], linewidths=0.7)
        ax.add_collection(lc)
    def nodes(ax, pts, fracs, base=26):
        xs_=[q[0] for q in pts]; ys_=[q[1] for q in pts]
        on=[fr>0 for fr in fracs]
        # dead first (hollow rings), then live (filled), so live sits on top
        d=[i for i,o in enumerate(on) if not o]
        if d: ax.scatter([xs_[i] for i in d],[ys_[i] for i in d],s=base,facecolors=DARK,edgecolors=RING,linewidths=.9,zorder=3)
        for i,fr in enumerate(fracs):
            if fr>0:
                ax.scatter([xs_[i]],[ys_[i]],s=base*(0.85+1.5*min(1,fr*6)),facecolors=LIT,edgecolors=LIT,
                           linewidths=.5,alpha=0.35+0.65*min(1,fr*6),zorder=4)
    nodes(ax,[pos[0][i] for i in pool_idx],[0.5]*len(pool_idx),base=16)
    nodes(ax,[pos[1][i] for i in range(H)],list(f1))
    nodes(ax,[pos[2][i] for i in range(H)],list(f2))
    nodes(ax,[pos[3][i] for i in range(ACT)],[0.6]*ACT,base=64)
    for x,lab in zip(xs,['pooled\ninput','hidden 1','hidden 2','actions']):
        ax.text(x,-0.04,lab,ha='center',va='top',fontsize=8.5,color='#d9c7a3')
    ax.set_xlim(-0.42,3.55); ax.set_ylim(-0.16,1.14); ax.axis('off')
    ax.set_title(title,fontsize=11,pad=8)
    ax.text(1.56,1.075,f'hidden 1: {alive1} / {H} firing    ·    hidden 2: {alive2} / {H} firing',
            ha='center',va='bottom',fontsize=8.5,color=GOLD)
    return alive1,alive2
DEAD='.probe/dead/dead-ckpt/card-tokens/seed-0/final.ckpt'
LIVE='/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt'
fig,ax=plt.subplots(figsize=(4.6,7.4))
d=draw(ax,load(DEAD),'dead','DEAD TRUNK  ·  600-scale reward')
fig.savefig('figures/network-dead.svg',transparent=True,bbox_inches='tight'); plt.close(fig)
fig.savefig('/tmp/fig-network-dead.png',facecolor='#14120f',bbox_inches='tight')
fig,ax=plt.subplots(figsize=(4.6,7.4))
l=draw(ax,load(LIVE),'live','LIVE TRUNK  ·  normalised reward')
fig.savefig('figures/network-live.svg',transparent=True,bbox_inches='tight'); plt.close(fig)
fig.savefig('/tmp/fig-network-live.png',facecolor='#14120f',bbox_inches='tight')
fig,axs=plt.subplots(1,2,figsize=(8.6,7.2))
for ax,path,t in zip(axs,(DEAD,LIVE),('DEAD TRUNK · 600-scale reward','LIVE TRUNK · normalised reward')):
    draw(ax,load(path),'',t)
fig.savefig('figures/network-compare.svg',transparent=True,bbox_inches='tight'); plt.close(fig)
fig.savefig('/tmp/fig-network-compare.png',facecolor='#14120f',bbox_inches='tight')
print('dead',d,'live',l)
