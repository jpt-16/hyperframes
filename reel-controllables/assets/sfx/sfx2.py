import numpy as np, wave
SR=48000; rng=np.random.default_rng(1808)
def write(name,x):
    x=x/np.max(np.abs(x))*10**(-6/20); st=np.stack([x,x],1)
    w=wave.open(name,"wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes()); w.close()
t_=lambda d: np.arange(int(d*SR))/SR
# thud v2: same damped low hit, plus a felted mid "knock" (~170 Hz body and a
# 900 Hz contact) so it survives a phone speaker that cannot play 60 Hz
t=t_(1.6); f=62+40*np.exp(-t/0.03); body=np.tanh(1.6*np.sin(2*np.pi*np.cumsum(f)/SR))*np.exp(-t/0.26)
knock=0.55*np.sin(2*np.pi*np.cumsum(170+60*np.exp(-t/0.02))/SR)*np.exp(-t/0.09)
contact=rng.standard_normal(len(t))*np.exp(-t/0.012)
write("_thud2.wav", body+knock+0.45*contact)
# crackle v2: denser, louder pops with more low-mid weight, so it reads
# between syllables instead of hiding under sibilance
T=2.6; t=t_(T); env=(t/T)**1.8; env[-int(.12*SR):]*=np.linspace(1,0,int(.12*SR))
x=np.zeros(len(t)); rate=14+90*env
for i in np.where(rng.random(len(t))<rate/SR)[0]:
    L=int(SR*rng.uniform(0.0008,0.004)); a=rng.exponential(0.7)*rng.choice([-1,1])
    seg=a*np.exp(-np.arange(L)/(L/4)); x[i:i+L]+=seg[:len(x)-i]
write("_crackle2.wav",(x+rng.standard_normal(len(t))*0.05)*env)
