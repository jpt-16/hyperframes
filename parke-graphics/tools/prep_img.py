"""Key the white studio background out of the blue Parke sweatshirt and upscale the small portraits.
    python3 tools/prep_img.py
"""
from PIL import Image, ImageFilter
import numpy as np
b = Image.open("assets/img/blue.jpg").convert("RGB")
a = np.asarray(b).astype(float)
d = 255 - a[..., 0]                       # the shirt is far from white in red; the studio bg is pure white
from scipy import ndimage as ndi
near_white = d < 14
lab, _ = ndi.label(near_white)
border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
bg = np.isin(lab, list(border))
bg = ndi.binary_dilation(bg, iterations=1)       # eat the 1px halo
alpha = (~bg).astype(float)
al = Image.fromarray((alpha * 255).astype("uint8")).filter(ImageFilter.MedianFilter(3))
big = b.resize((1340, 1340), Image.LANCZOS)
al = al.resize((1340, 1340), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.8))
out = big.copy(); out.putalpha(al)
bb = out.getbbox(); out = out.crop(bb); out.save("assets/img/blue_cut.png"); print("blue_cut", out.size, bb)
for n, s in (("forbes", 3), ("portrait", 2)):
    im = Image.open(f"assets/img/{n}.jpg").convert("RGB")
    im.resize((im.width * s, im.height * s), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 2)).save(f"assets/img/{n}_x.jpg", quality=92)
g = Image.open("assets/img/grey.jpg").convert("RGB")
g.save("assets/img/grey_x.jpg", quality=92)
