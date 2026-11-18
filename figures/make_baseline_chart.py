"""Naive model vs the deterministic/random baselines, with a live model as contrast."""
import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({'svg.fonttype':'none','axes.facecolor':'none','figure.facecolor':'none',
                     'savefig.facecolor':'none','text.color':'#f2e8d5','font.size':10,
                     'axes.edgecolor':'#d9c7a3','axes.labelcolor':'#f2e8d5','xtick.color':'#d9c7a3',
                     'ytick.color':'#d9c7a3','axes.titlecolor':'#f2e8d5'})
GOLD,SKY,RED,SLATE='#d9a441','#6fa8dc','#d4553f','#8a8378'
naive=json.load(open('.probe/naive-vs-baselines.json'))
live=json.load(open('.probe/live-vs-baselines.json'))
ORDER=['fold-large-bet','random','always-call','oracle','fold-no-pair-or-face','fold-no-pair-or-better']
LAB={'fold-large-bet':'fold-large-bet','random':'random','always-call':'always-call',
     'oracle':'oracle (equity)','fold-no-pair-or-face':'fold: no pair or face',
     'fold-no-pair-or-better':'fold: no pair or better'}
fig,ax=plt.subplots(figsize=(7.6,4.2))
y=np.arange(len(ORDER)); h=0.36
nv=[naive[o]['chips'] for o in ORDER]; nc=[naive[o]['ci'] for o in ORDER]
lv=[live[o]['chips'] for o in ORDER]; lc=[live[o]['ci'] for o in ORDER]
ax.barh(y-h/2,nv,xerr=nc,height=h,color=SKY,capsize=3,error_kw=dict(ecolor='#f2e8d5',lw=1),
        label='naive model  ·  flat numbers, plain stack')
ax.barh(y+h/2,lv,xerr=lc,height=h,color=GOLD,capsize=3,error_kw=dict(ecolor='#f2e8d5',lw=1),
        label='live model  ·  token embedding, normalised reward')
ax.axvline(0,color='#f2e8d5',lw=.9,ls=':')
ax.set_yticks(y); ax.set_yticklabels([LAB[o] for o in ORDER])
ax.set_xlabel('chips per hand for the model  ·  five copies of that baseline at a six-seat table')
ax.set_xlim(-32,26)
for i,(a,b) in enumerate(zip(nv,lv)):
    ax.text(a+(nc[i] if a>=0 else -nc[i])+(0.6 if a>=0 else -0.6),i-h/2-0.10,f'{a:+.1f}',va='center',
            ha='left' if a>=0 else 'right',fontsize=8.5,color=SKY)
    ax.text(b+(lc[i] if b>=0 else -lc[i])+(0.6 if b>=0 else -0.6),i+h/2+0.10,f'{b:+.1f}',va='center',
            ha='left' if b>=0 else 'right',fontsize=8.5,color=GOLD)
ax.legend(frameon=False,loc='lower center',bbox_to_anchor=(.5,-.36),ncol=1,fontsize=9)
ax.set_title('Neither model beats a selective opponent  ·  1,000 hands per cell')
ax.spines[['top','right']].set_visible(False)
fig.savefig('figures/naive-vs-baselines.svg',transparent=True,bbox_inches='tight')
fig.savefig('/tmp/fig-naive-baselines.png',facecolor='#14120f',bbox_inches='tight')
m=json.load(open('figures/manifest.json'))
m['naive-vs-baselines']={'title':'Naive model vs the baselines',
 'caption':'The naive model (flat numbers, plain stack) against each deterministic or random baseline, with a live token-embedding model beside it. Both beat the trivial opponents and both lose to the selective ones; the live model raises on three quarters of its decisions and is punished hardest.',
 'provenance':'trained for this figure at six seats (flat-numeric + naive-stack, 5,000 hands) and /tmp/foldloop/high; 1,000 hands per cell, 95% CI',
 'alt':'Grouped horizontal bars of chips per hand for twenty-four cells: two models against six opponents.','file':'naive-vs-baselines.svg'}
json.dump(m,open('figures/manifest.json','w'),indent=1)
print('wrote naive-vs-baselines.svg')
