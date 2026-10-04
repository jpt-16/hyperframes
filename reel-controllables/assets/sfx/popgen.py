import numpy as np, wave
SR=48000; rng=np.random.default_rng(612)
def write(name,x):
    st=np.stack([x,x],1); st=st/np.max(np.abs(st))*0.5
    w=wave.open(name,"wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes()); w.close()
T=lambda d: np.arange(int(d*SR))/SR
# a soft bubble pop: a sine whose pitch falls fast, a 1 ms lip click, no reverb
def pop(f0,f1,glide,tau,d=0.16):
    t=T(d); f=f1+(f0-f1)*np.exp(-t/glide); ph=2*np.pi*np.cumsum(f)/SR
    body=np.sin(ph)*np.exp(-t/tau)*np.minimum(1,t/0.0008)
    click=rng.standard_normal(len(t))*np.exp(-t/0.0012)*0.25
    k=np.ones(6)/6; click=np.convolve(click,k,"same")    # take the fizz off the click
    return body+click
write("pop_in.wav", pop(1150,330,0.012,0.028))
write("pop_out.wav", pop(380,620,0.02,0.022)*0.8)   # rising, smaller: the print leaving
