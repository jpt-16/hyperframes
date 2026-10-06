import subprocess, os, json
U="/root/.claude/uploads/c2b5e160-f243-5674-b7e5-e3357c59e48b"
S=os.path.dirname(os.path.abspath(__file__)); P=f"{S}/prep"; os.makedirs(P,exist_ok=True)
CLIPS={"IMG_1842":"5f088d00-IMG_1842_compressed.mp4","IMG_1853":"326b58da-IMG_1853_compressed.mp4",
 "IMG_1856":"267b6e49-IMG_1856.mov","IMG_1861":"57b844ed-IMG_1861_compressed.mp4",
 "IMG_1863":"44c8eca8-IMG_1863_compressed.mp4","IMG_1866":"82e08083-IMG_1866_compressed.mp4"}
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
def run(c): subprocess.run(c,check=True)
for k,f in CLIPS.items():
    src=f"{U}/{f}"
    # one decode: picture (tone-mapped, cover-cropped, CFR) + untouched 48k audio as PCM, same timeline
    run(["ffmpeg","-v","error","-y","-i",src,"-vf",f"{TM},scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,setsar=1",
         "-c:v","libx264","-preset","fast","-crf","12","-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709",
         "-c:a","pcm_s16le","-ar","48000","-ac","2",f"{P}/{k}.mov"])
    run(["ffmpeg","-v","error","-y","-i",f"{P}/{k}.mov","-vn","-ac","1","-ar","16000",f"{P}/{k}_16k.wav"])
    print(k, subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"{P}/{k}.mov"],capture_output=True,text=True).stdout.strip(), flush=True)
