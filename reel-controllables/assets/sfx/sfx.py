import numpy as np, wave, subprocess
SR=48000; rng=np.random.default_rng(1808)          # fixed seed: reproducible
def write(name,x):
    x=x/np.max(np.abs(x))*10**(-6/20)               # peak -6 dBFS; level set in the mix
    st=np.stack([x,x],1)
    pcm=(st*32767).astype(np.int16).tobytes()
    w=wave.open(name,"wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm); w.close()
def t_(d): return np.arange(int(d*SR))/SR
# 1. cinematic sub-boom: 58 -> 34 Hz glide, slow decay. tanh saturation adds the
#    80-160 Hz harmonics that let a phone speaker carry what is otherwise sub.
t=t_(3.4); f=34+24*np.exp(-t/0.35); ph=2*np.pi*np.cumsum(f)/SR
att=np.clip(t/0.035,0,1); att=0.5-0.5*np.cos(np.pi*att)
boom=np.tanh(1.8*np.sin(ph))*att*np.exp(-t/1.15)
write("_boom.wav",boom)
# 2. analog thud: soft felted low hit + dull transient, like a damped kick
t=t_(1.6); f=62+40*np.exp(-t/0.03); ph=2*np.pi*np.cumsum(f)/SR
body=np.tanh(1.4*np.sin(ph))*np.exp(-t/0.26)
n=rng.standard_normal(len(t))*np.exp(-t/0.018)
thud=body+0.35*n
write("_thud.wav",thud)
# 3. vinyl crackle swell: crackle density and hiss both rise into the turn
T=2.6; t=t_(T); env=(t/T)**2.2; env[-int(.12*SR):]*=np.linspace(1,0,int(.12*SR))
x=np.zeros(len(t))
rate=8+55*env
for i in np.where(rng.random(len(t))<rate/SR)[0]:
    L=int(SR*rng.uniform(0.0006,0.003)); a=rng.exponential(0.5)*rng.choice([-1,1])
    seg=a*np.exp(-np.arange(L)/(L/4)); x[i:i+L]+=seg[:len(x)-i]
hiss=rng.standard_normal(len(t))*0.06
write("_crackle.wav",(x+hiss)*env)
