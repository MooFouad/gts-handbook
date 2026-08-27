"""Build imgmanifest.json from the fresh Playwright captures.
- downscale to manifest width, blur only genuinely-sensitive regions, regenerate thumbnails.
"""
import base64, io, json, os
from PIL import Image, ImageFilter
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CAP  = os.path.join(HERE, "captures")
MANP = os.path.join(HERE, "imgmanifest.json")
W    = 1500          # manifest image width
TW   = 250           # thumbnail width

# capture file -> manifest page key
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

def enc(im, width, q=88):
    im=im.convert("RGB")
    if im.width!=width: im=im.resize((width,round(im.height*width/im.width)),Image.LANCZOS)
    bio=io.BytesIO(); im.save(bio,"JPEG",quality=q,optimize=True)
    return "data:image/jpeg;base64,"+base64.b64encode(bio.getvalue()).decode()

man = {}

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
bio = io.BytesIO(); chip.save(bio, "PNG")
man["logo"] = "data:image/png;base64,"+base64.b64encode(bio.getvalue()).decode()

# ── favicon: same mark, padded into a square, embedded into the manifest ──
side = max(mark.width, mark.height)
fav_pad = int(side * 0.14)
fav_canvas = Image.new("RGBA", (side + fav_pad*2, side + fav_pad*2), (0,0,0,0))
fav_canvas.paste(mark, (fav_pad + (side-mark.width)//2, fav_pad + (side-mark.height)//2), mark)
for size, key in [(32,"favicon32"), (180,"favicon180")]:
    icon = fav_canvas.resize((size,size), Image.LANCZOS)
    icon.save(os.path.join(HERE, "assets", f"favicon-{size}.png"))
    bio = io.BytesIO(); icon.save(bio, "PNG")
    man[key] = "data:image/png;base64,"+base64.b64encode(bio.getvalue()).decode()

def add(key, im):
    if key in BLUR: blur(im, BLUR[key])
    man[key]=enc(im, W)
    man["thumb_"+key]=enc(im, TW, q=72)

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
man["page_payroll"]=enc(im, W)
man["thumb_page_payroll"]=enc(im, TW, q=72)
print("ok page_payroll (single, full height)", h)

json.dump(man, open(MANP,"w"))
print("keys:",len(man))
