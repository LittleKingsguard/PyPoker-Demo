"""Presentation figures for the PyPoker project. Every number is sourced from a decision row (D-n)
or a record in strata/records/; nothing here is computed fresh or invented.
Writes SVG into figures/ plus figures/manifest.json (title, caption, provenance, alt text).
Palette: transparent background, bright on dark (the deck is felt-themed)."""
import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
plt.rcParams.update({'svg.fonttype':'none','font.size':11,'axes.edgecolor':'#d9c7a3',
                     'axes.labelcolor':'#f2e8d5','text.color':'#f2e8d5','xtick.color':'#d9c7a3',
                     'ytick.color':'#d9c7a3','axes.titlecolor':'#f2e8d5','figure.dpi':110,
                     'axes.facecolor':'none','figure.facecolor':'none','savefig.facecolor':'none'})
GOLD,EMERALD,CRIMSON,SLATE,SKY='#d9a441','#4fbf8b','#d4553f','#8a8378','#6fa8dc'
FIG={}
def save(fig,name,title,caption,provenance,alt):
    fig.savefig(f'figures/{name}.svg', transparent=True, bbox_inches='tight')
    fig.savefig(f'/tmp/fig-{name}.png', facecolor='#14120f', bbox_inches='tight')  # inspection only
    plt.close(fig)
    FIG[name]={'title':title,'caption':caption,'provenance':provenance,'alt':alt,'file':f'{name}.svg'}
    print('wrote', name+'.svg')
# 1 signal by street -------------------------------------------------------------
fig,ax=plt.subplots(figsize=(6.4,3.4))
streets=['preflop\n(2 cards)','flop\n(5)','turn\n(6)','river\n(7)']; vals=[2.4,14.4,20.9,52.8]
b=ax.bar(streets,vals,color=[SLATE,SKY,SKY,EMERALD],width=.62)
for r,v in zip(b,vals): ax.text(r.get_x()+r.get_width()/2,v+1.2,f'{v:.1f}%',ha='center',fontweight='bold')
ax.set_ylabel('six-way outcome variance explained'); ax.set_ylim(0,60)
ax.set_title('The signal arrives with the board'); ax.spines[['top','right']].set_visible(False)
save(fig,'signal-by-street','Signal by street','How much of a six-way showdown the cards explain, by how many are known.',
     'D-83, D-86, D-93','Bars: 2.4% preflop, 14.4% flop, 20.9% turn, 52.8% river.')
# 2 representation ladder -------------------------------------------------------
fig,ax=plt.subplots(figsize=(6.8,3.6))
names=['tokens + mean pool','tokens + positions + mean','flat one-hot (433)','attention + positions (120 ep)','attention + positions (400 ep)']
vals=[13.1,15.3,20.4,32.4,40.0]; cols=[CRIMSON,CRIMSON,SLATE,EMERALD,GOLD]
y=range(len(names))
ax.barh(list(y),vals,color=cols)
for i,v in enumerate(vals): ax.text(v+0.6,i,f'{v:.1f}%',va='center',fontweight='bold')
ax.set_yticks(list(y)); ax.set_yticklabels(names); ax.invert_yaxis()
ax.set_xlabel('outcome variance explained'); ax.set_xlim(0,46)
ax.set_title('What each representation buys'); ax.spines[['top','right']].set_visible(False)
save(fig,'representation-ladder','Representation ladder','The same target, five encodings. Attention with positions wins; the embedding buys the ceiling, not the mechanism.',
     'D-84, D-86, D-87, D-88, D-89, D-93, D-96','Horizontal bars from 13.1% (mean pool) to 40.0% (attention, 400 epochs).')
# 3 convergence -----------------------------------------------------------------
fig,ax=plt.subplots(figsize=(6.4,3.4))
ep=[20,60,120,160,200,240,320,360,400]; r2=[25.13,28.14,32.37,34.04,34.09,35.58,37.83,40.16,39.99]
ax.plot(ep,r2,marker='o',color=GOLD,lw=2.2)
ax.scatter([60],[28.14],s=90,facecolor='none',edgecolor=CRIMSON,lw=2,zorder=5)
ax.annotate('60-epoch snapshot\nquoted in early results',(60,28.14),xytext=(95,22.5),
            arrowprops=dict(arrowstyle='->',color=CRIMSON),color=CRIMSON,fontsize=9)
ax.set_xlabel('training epochs'); ax.set_ylabel('outcome variance explained (%)')
ax.set_ylim(20,44); ax.set_title('The curve, not the point'); ax.spines[['top','right']].set_visible(False)
save(fig,'card-model-convergence','Card model convergence','Every early figure was a snapshot: the model was still improving at 320 epochs and flattened at 360-400.',
     'D-85, D-93','Line: R-squared rises from 25% at 20 epochs to 40% at 360, with the 60-epoch snapshot marked.')
# 4 battery: predicted vs true ---------------------------------------------------
fig,ax=plt.subplots(figsize=(6.8,3.6))
hands=['quad aces','nut flush','straight','trip aces','pair of kings','2-3 junk','2-7 junk']
true=[100,100,97.8,91.8,45.1,0.0,0.0]; pred=[99.66,99.65,11.21,2.71,28.03,0.0,0.0]
x=range(len(hands)); w=.38
ax.bar([i-w/2 for i in x],true,w,label='true equity (Monte Carlo)',color=SLATE)
ax.bar([i+w/2 for i in x],pred,w,label='model, 400 epochs',color=CRIMSON)
ax.set_xticks(list(x)); ax.set_xticklabels(hands,rotation=18,ha='right')
ax.set_ylabel('win probability (%)'); ax.legend(frameon=False,loc='upper right',fontsize=9)
ax.set_title('The aggregate hid an 89-point error'); ax.spines[['top','right']].set_visible(False)
save(fig,'battery-error','Extremes battery','The converged card model predicts 2.7% for trip aces whose true equity is 91.8% — the failure a pooled R-squared could not show.',
     'D-91, D-94, D-95','Grouped bars comparing true and predicted equity across seven verified extreme hands.')
# 5 chips ladder -----------------------------------------------------------------
fig,ax=plt.subplots(figsize=(7.0,3.6))
names=['fold every hand','product, net-chips','probe, eps 0.05','probe, eps 0.60','eps 0.60 + opponent model']
vals=[-0.60,1.82,3.68,11.30,12.92]; errs=[0.04,8.81,3.21,4.16,5.28]
cols=[SLATE,SLATE,SKY,EMERALD,GOLD]
ax.barh(range(len(names)),vals,xerr=errs,color=cols,capsize=4,error_kw=dict(ecolor='#f2e8d5',lw=1.2))
ax.axvline(0,color='#f2e8d5',lw=.8,ls=':')
for i,(v,e) in enumerate(zip(vals,errs)):
    ax.text(v+(e if v>=0 else -e)+(0.5 if v>=0 else -0.5),i,f'{v:+.1f}',va='center',
            ha='left' if v>=0 else 'right',fontweight='bold')
ax.set_yticks(range(len(names))); ax.set_yticklabels(names); ax.invert_yaxis()
ax.set_xlabel('chips per hand against the league (95% CI)'); ax.set_xlim(-9,25)
ax.set_title('The exploration floor is the mechanism'); ax.spines[['top','right']].set_visible(False)
save(fig,'chips-ladder','Chips per hand','Same representation, same pooler, same league: the epsilon floor moves the agent from folding every hand to a mixed policy worth +11 to +13 chips per hand.',
     'D-72, D-105, D-125, D-126','Horizontal bars with error bars: fold -0.6, product +1.8, eps 0.05 +3.7, eps 0.60 +11.3, +opponent model +12.9.')
# 6 trunk health -----------------------------------------------------------------
fig,ax=plt.subplots(figsize=(5.8,3.2))
grp=['600-scale reward','normalised reward']; alive=[0,22]; units=50
ax.bar(grp,[units,units],color='#2a2622',label='dead units')
ax.bar(grp,alive,color=EMERALD,label='live units')
for i,v in enumerate(alive): ax.text(i,v+1.5,f'{v}/50 alive',ha='center',fontweight='bold')
ax.set_ylabel('hidden units in layer 1'); ax.set_ylim(0,56); ax.legend(frameon=False,loc='upper left',fontsize=9)
ax.set_title('A network that computes nothing'); ax.spines[['top','right']].set_visible(False)
save(fig,'trunk-health','Dead trunk','At the 600-scale reward every hidden unit was dead and the policy was a constant; the normalised reward revives 22 of 50.',
     'D-60, D-67, D-108','Two stacked bars: 0 of 50 live units under the 600-scale reward, 22 of 50 under the normalised reward.')
# 7 monotonicity -----------------------------------------------------------------
fig,ax=plt.subplots(figsize=(6.8,3.6))
pts=[('72o',6.8,0),('32o',9.3,0),('82o',10.6,0),('72s',10.5,2),('43s',12.2,2),('22',12.3,0),
     ('87s',19.3,1),('KQo',22.8,2),('T9s',25.2,1),('AKo',30.8,2),('QQ',41.1,1),('AA',50.9,2)]
lbl={0:'fold',1:'call',2:'raise'}
for col,mark in ((0,CRIMSON),(1,SKY),(2,GOLD)):
    xs=[p[1] for p in pts if p[2]==col]; ys=[p[2] for p in pts if p[2]==col]
    ax.scatter(xs,ys,s=110,color=mark,label=lbl[col],zorder=3)
offs=[(-7,10),(-7,-16),(7,10),(7,-16)]
for i,(n,x,y) in enumerate(sorted(pts,key=lambda q:(q[2],q[1]))):
    dx,dy=offs[i%len(offs)]
    ax.annotate(n,(x,y),xytext=(dx,dy),textcoords='offset points',fontsize=9,
                ha='left' if dx>0 else 'right')
ax.set_yticks([0,1,2]); ax.set_yticklabels(['fold','call','raise'])
ax.set_xlabel('true preflop equity (%)'); ax.set_ylim(-.6,2.6); ax.set_xlim(2,56)
ax.legend(frameon=False,loc='lower center',bbox_to_anchor=(.5,-.42),ncol=3,fontsize=9)
ax.set_title('Reads the cards, does not rank them'); ax.spines[['top','right']].set_visible(False)
save(fig,'monotonicity','Monotonicity','Aggression should rise with equity. Suited junk is shoved while a small pair folds, and queens are called while an offsuit ace is shoved: 12 violations.',
     'D-116, D-127','Scatter of action (fold, call, raise) against true equity for twelve hole sets, showing inversions.')
# 8 padding ----------------------------------------------------------------------
fig,ax=plt.subplots(figsize=(6.4,2.4))
ax.barh([0],[14],color=EMERALD,label='14 real tokens')
ax.barh([0],[108],left=[14],color='#3a352e',label='108 padding positions')
ax.text(7,0,'14',ha='center',va='center',fontweight='bold',color='#0d0b09')
ax.text(14+54,0,'108 pad  (89%)',ha='center',va='center',fontweight='bold')
ax.set_yticks([]); ax.set_xlim(0,122); ax.set_xlabel('token positions in one six-seat observation')
ax.legend(frameon=False,loc='lower center',bbox_to_anchor=(.5,-.75),ncol=2,fontsize=9)
ax.set_title('88% of the input was the token for "nothing here"'); ax.spines[['top','right','left']].set_visible(False)
save(fig,'padding','Padding composition','A six-seat observation is 122 tokens; a preflop decision uses 14. The unmasked pool averaged the other 108 into every decision.',
     'D-78, D-79, D-110','Stacked bar: 14 real tokens and 108 padding positions out of 122.')
json.dump(FIG,open('figures/manifest.json','w'),indent=1)
print(f'\n{len(FIG)} figures + manifest.json')
