"""Build img/ from the fresh Playwright captures.
- downscale, blur only genuinely-sensitive regions, regenerate thumbnails.
- writes real image FILES into img/ (not inlined base64) so handbook.html
  stays tiny and each slide's image is fetched on demand.
"""
import os
from PIL import Image, ImageFilter
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CAP  = os.path.join(HERE, "captures")
IMGDIR = os.path.join(HERE, "img")
os.makedirs(IMGDIR, exist_ok=True)
W    = 1500          # page image width
TW   = 250            # thumbnail width

# capture file -> output key
MAP = {
 "login_main":"page_login_main", "login_temp":"page_login_temp",
 "dash":"page_dash_full", "myprofile":"page_myprofile", "attendance":"page_attendance",
 "joinreports":"page_joinreports", "statistics":"page_statistics", "payment":"page_payment",
 "pettycash":"page_pettycash", "businesstrips":"page_businesstrips", "tdy":"page_tdy",
 "airtickets":"page_airtickets", "exit":"page_exit", "leave":"page_leave",
 "vacations":"page_vacations", "insurance":"page_insurance", "support":"page_support",
 "performance":"page_performance",
}
# sensitive blur rectangles (fractions of the image: l,t,r,b)
BLUR = {
 "page_myprofile":  [(0.51,0.345,0.60,0.375),(0.705,0.50,0.85,0.535)],  # phone, personal email
 "page_payment":    [(0.21,0.375,0.402,0.955)],                         # beneficiary + amount cols
 "page_statistics": [(0.10,0.725,0.21,0.775)],                          # Current Package amount only
}

def blur(im, rects):
    w,h=im.size
    for l,t,r,b in rects:
        L,T,R,B=int(l*w),int(t*h),int(r*w),int(b*h)
        if R<=L or B<=T: continue
        rad=min(28, max(8,int((B-T)*0.30)))
        reg=im.crop((L,T,R,B)).filter(ImageFilter.GaussianBlur(rad))
        im.paste(reg,(L,T))

def save(im, path, width, q=88):
    im=im.convert("RGB")
    if im.width!=width: im=im.resize((width,round(im.height*width/im.width)),Image.LANCZOS)
    im.save(path, "JPEG", quality=q, optimize=True, progressive=True)

def add(key, im):
    if key in BLUR: blur(im, BLUR[key])
    save(im, os.path.join(IMGDIR, key+".jpg"), W, 88)
    save(im, os.path.join(IMGDIR, "thumb_"+key+".jpg"), TW, 72)

# ── logo: crop the "GTS + flag" mark from the horizontal lockup (real alpha
#    already baked in) — no need to fake transparency, just tight-crop it ──
LOGO = os.path.join(HERE, "assets", "GTS Logo Horizontal.png")
lg = Image.open(LOGO).convert("RGBA")
lw, lh = lg.size
mark_area = lg.crop((0, 0, min(lw, int(lw*0.50)), lh))   # left half: GTS wordmark + flag stripes, no text
ma = np.asarray(mark_area)
mask = ma[..., 3] > 10
ys, xs = np.where(mask)
m = 10
bx0, bx1 = max(0, xs.min()-m), min(mark_area.width, xs.max()+m)
by0, by1 = max(0, ys.min()-m), min(mark_area.height, ys.max()+m)
mark = mark_area.crop((bx0, by0, bx1, by1))
pad_x, pad_y = 8, 8
chip = Image.new("RGBA", (mark.width+pad_x*2, mark.height+pad_y*2), (0,0,0,0))
chip.paste(mark, (pad_x, pad_y), mark)
chip.save(os.path.join(IMGDIR, "logo.png"))

# ── favicon: the full wordmark is too wide to read at 32px, so use just the
#    flag-stripe block (the part right of "GTS") — compact, colorful, square-friendly ──
gap_scan = mark_area.crop((700, 0, mark_area.width, mark_area.height))
ga = np.asarray(gap_scan)
gmask = ga[..., 3] > 10
gcols = np.where(gmask.any(axis=0))[0]
ggaps = np.diff(gcols)
split = 700 + gcols[np.argmax(ggaps)] + ggaps.max() // 2   # midpoint of the gap after "GTS"
flag_area = mark_area.crop((split, 0, mark_area.width, mark_area.height))
fa = np.asarray(flag_area)
fmask = fa[..., 3] > 10
fys, fxs = np.where(fmask)
flag = flag_area.crop((fxs.min(), fys.min(), fxs.max(), fys.max()))

side = max(flag.width, flag.height)
fav_pad = int(side * 0.16)
fav_canvas = Image.new("RGBA", (side + fav_pad*2, side + fav_pad*2), (0,0,0,0))
fav_canvas.paste(flag, (fav_pad + (side-flag.width)//2, fav_pad + (side-flag.height)//2), flag)
for size in (32, 180):
    fav_canvas.resize((size,size), Image.LANCZOS).save(os.path.join(IMGDIR, f"favicon-{size}.png"))

# regular pages
for f,key in MAP.items():
    p=os.path.join(CAP,f+".png")
    if not os.path.exists(p): print("MISSING",p); continue
    add(key, Image.open(p).convert("RGB"))
    print("ok",key)

# payroll -> ONE full-page slide; blur only money figures throughout
im=Image.open(os.path.join(CAP,"payroll.png")).convert("RGB"); w,h=im.size
a=np.asarray(im.convert("L"))
def gap(target,win=220):
    lo=max(1,target-win); hi=min(h-1,target+win); best=target; bs=-1
    for y in range(lo,hi):
        r=a[y]; s=r.mean()-r.std()
        if s>bs: bs=s; best=y
    return best
c1,c2,c3 = gap(2100), gap(4950), gap(11300)
def seg_rect(y0,y1,l,t,r,b):
    sh=y1-y0
    return (l, (y0+t*sh)/h, r, (y0+b*sh)/h)
payroll_blur = [
 seg_rect(0,c1,   0.53,0.71,0.96,0.77),   # package legend amounts
 seg_rect(0,c1,   0.28,0.86,0.44,0.925),  # total payable (overview card)
 seg_rect(c1,c2,  0.09,0.83,0.20,0.875),  # basic daily rate
 seg_rect(c1,c2,  0.33,0.925,0.45,0.965), # full daily rate
 seg_rect(c3,h,   0.475,0.27,0.635,0.91), # summary amount column + total payable
]
blur(im, payroll_blur)
save(im, os.path.join(IMGDIR, "page_payroll.jpg"), W, 88)
save(im, os.path.join(IMGDIR, "thumb_page_payroll.jpg"), TW, 72)
print("ok page_payroll (single, full height)", h)

print("done -> img/")
