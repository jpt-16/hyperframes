import sherpa_onnx, wave, numpy as np, json, sys, os
M="/tmp/claude-0/-home-user-hyperframes/c2b5e160-f243-5674-b7e5-e3357c59e48b/scratchpad/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
rec=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{M}/encoder.int8.onnx",decoder=f"{M}/decoder.int8.onnx",
    joiner=f"{M}/joiner.int8.onnx",tokens=f"{M}/tokens.txt",model_type="nemo_transducer",num_threads=4)
P=os.path.dirname(os.path.abspath(__file__))+"/prep"; out={}
for k in sys.argv[1:]:
    w=wave.open(f"{P}/{k}_16k.wav"); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
    s=rec.create_stream(); s.accept_waveform(16000,a); rec.decode_stream(s); r=s.result
    words=[]; 
    for tok,t in zip(r.tokens,r.timestamps):
        if tok.startswith(" ") or not words: words.append({"text":tok.strip(),"start":round(float(t),3)})
        else: words[-1]["text"]+=tok
    for i,wd in enumerate(words):
        wd["end"]=round(words[i+1]["start"] if i+1<len(words) else min(wd["start"]+0.5,len(a)/16000),3)
    out[k]=words; print(k, r.text, flush=True)
json.dump(out,open(f"{P}/../words.json","w"),indent=0)
