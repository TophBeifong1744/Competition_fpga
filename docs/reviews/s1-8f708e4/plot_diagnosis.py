import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).parent
d=json.loads((ROOT/'diagnosis.json').read_text())
a=np.loadtxt(str(ROOT/'short-time-rms.csv'),delimiter=',',skiprows=1)
fig,axes=plt.subplots(2,1,figsize=(11,7))
for c in range(4):axes[0].plot(a[:,0],a[:,c+1],label='mic'+str(c),linewidth=.9)
for t in [2,5]:axes[0].axvline(t,color='black',linestyle='--',alpha=.55)
axes[0].set_title('S1: 20 ms demeaned RMS / dashed lines = approximate operator timing')
axes[0].set_ylabel('Original PCM codes');axes[0].set_xlabel('Seconds at configured 48 kHz')
axes[0].legend(ncol=4);axes[0].grid(alpha=.2)
labels=['0-100 Hz','100-300 Hz','300-3400 Hz','3.4-8 kHz','8-24 kHz']
colors=['#455a64','#607d8b','#1976d2','#42a5f5','#bbdefb']
bottom=np.zeros(3)
for b in range(5):
    vals=np.array([np.mean(s['fraction_of_windowed_power'][b])*100 for s in d['band_observations']])
    axes[1].bar(np.arange(3),vals,bottom=bottom,label=labels[b],color=colors[b]);bottom+=vals
axes[1].set_xticks(np.arange(3));axes[1].set_xticklabels(['Nominal 0-2 s','Nominal 2-5 s','Nominal 5 s-end'])
axes[1].set_ylabel('Mean channel windowed power (%)');axes[1].set_ylim(0,100)
axes[1].set_title('Descriptive band shares: not SNR or acoustic activity labels')
axes[1].legend(loc='center left',bbox_to_anchor=(1,0.5))
fig.tight_layout();fig.savefig(str(ROOT/'diagnostic.png'),dpi=150,bbox_inches='tight');plt.close(fig)
