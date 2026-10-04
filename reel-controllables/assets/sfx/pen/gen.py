import numpy as np, wave
SR=48000; rng=np.random.default_rng(1826)
def write(name,x):
    st=np.stack([x,x],1); st=st/np.max(np.abs(st))*0.5
    w=wave.open(name,"wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes()); w.close()
T=lambda d: np.arange(int(d*SR))/SR
def speed(d):            # derivative of GSAP power2.inOut = the pen's velocity
    u=T(d)/d; return np.where(u<.5, 4*u, 4*(1-u))
def scratch(d, rough=1.0):
    n=rng.standard_normal(int(d*SR))
    grain=1+rough*0.6*np.sign(np.sin(2*np.pi*np.cumsum(rng.uniform(90,260,len(n)))/SR))  # paper tooth
    return n*grain
# pen stroke matched to a draw of duration d, plus a short lift-off tail
def stroke(d):
    x=scratch(d)*(0.15+0.85*speed(d)); tail=scratch(0.08)*np.linspace(.2,0,int(.08*SR))
    return np.concatenate([x,tail])
# handwriting: the same scratch, gated into letter-sized bursts
def writing(d):
    x=scratch(d,1.3); g=np.zeros(len(x)); i=0; on=True
    while i<len(x):
        L=int(SR*(rng.uniform(.035,.09) if on else rng.uniform(.012,.035)))
        if on: g[i:i+L]=np.hanning(min(L,len(x)-i)) if L>8 else 0
        i+=L; on=not on
    return x*g*(0.4+0.6*np.minimum(1,T(d)/0.08))
# felt-tip tap: dull contact + a little paper body, pitched per row
def tap(p):
    t=T(0.22); click=rng.standard_normal(len(t))*np.exp(-t/0.0035)
    body=np.sin(2*np.pi*(190*p)*t)*np.exp(-t/0.03)*0.6
    return click+body
# the payoff check: short down-stroke, then a quicker, brighter flick up
def check():
    a=scratch(.13)*np.hanning(int(.13*SR)); b=scratch(.27,1.4)*np.linspace(.3,1.2,int(.27*SR))
    b[-int(.05*SR):]*=np.linspace(1,0,int(.05*SR))
    return np.concatenate([a,np.zeros(int(.03*SR)),b])
# paper rustle as the list comes back
def rustle():
    d=0.55; x=scratch(d,0.4)*np.hanning(int(d*SR)); return x
write("stroke_07.wav",stroke(0.7)); write("stroke_06.wav",stroke(0.6))
write("write_05.wav",writing(0.5)); write("write_06.wav",writing(0.6)); write("write_055.wav",writing(0.55))
for i,p in enumerate([1.0,1.06,1.12,1.19]): write(f"tap{i}.wav",tap(p))
write("check.wav",check()); write("rustle.wav",rustle())
