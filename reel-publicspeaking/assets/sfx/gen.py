import numpy as np, wave
SR=48000; rng=np.random.default_rng(1863)
def write(name,x):
    st=np.stack([x,x],1); st=st/np.max(np.abs(st))*0.708     # -3 dBFS, after all shaping
    w=wave.open(name,"wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes()); w.close()
T=lambda d: np.arange(int(d*SR))/SR
def lp(x,a):                          # one-pole low-pass, a in (0,1): smaller = darker
    y=np.empty_like(x); s=0.0
    for i,v in enumerate(x): s+=a*(v-s); y[i]=s
    return y
# stage light: the switch throw (two clicks 9 ms apart), a dull body as the
# lamp housing takes it, then a faint mains hum as the filament warms
def stagelight(d=1.1):
    t=T(d); x=np.zeros(len(t))
    for off,amp in [(0.0,1.0),(0.009,0.6)]:
        i=int(off*SR); n=int(0.006*SR)
        x[i:i+n]+=lp(rng.standard_normal(n),0.35)*np.exp(-np.arange(n)/SR/0.0012)*amp
    body=np.sin(2*np.pi*72*t)*np.exp(-t/0.07)*0.55+np.sin(2*np.pi*143*t)*np.exp(-t/0.04)*0.25
    hum=sum(np.sin(2*np.pi*120*h*t)/h for h in (1,2,3,5))*0.05
    hum*=np.clip((t-0.04)/0.25,0,1)*np.exp(-np.clip(t-0.3,0,None)/0.3)
    return x+body+hum
write("stagelight.wav",stagelight())
