"""Plans 0:19,65-0:40,8 : l'ouroboros, l'amphore de Dédale et le Discobole, le soleil, David, la Création, Atlas,
la foudre, l'escalier, la torche, la statue, la descente, les Anunnaki, les deux torches, la bascule des figures."""
import math, functools
import numpy as np, skia, cv2
from engine.core import *
from engine.common import *
from engine.shots_a import fit_h, alpha_extent, ochre_world, HOOK_HILLS, GROUND, place

DARK = (14, 10, 8)

def dark_bg(c, col_=DARK, glow_c=None, gx=640, gy=360, gr=520, ga=0.15):
    c.drawRect(skia.Rect(0, 0, W, H), fill_paint(col_))
    if glow_c: glow(c, gx, gy, gr, glow_c, ga)

# ---------- l'ouroboros (gravure réelle, en or, qui tourne lentement) ----------
def s_ouroboros(c, lt, d, T, p):
    dark_bg(c, glow_c=GOLD, ga=0.10)
    stars(c, T, seed=4, a=0.35, dx=-6 * lt)
    img = asset("ouroboros_gold"); s = 640 / img.width() * (1 + 0.015 * pulse(T) + 0.03 * lt / d)
    c.save(); c.translate(640, 360); c.rotate(-9 * T); c.translate(-640, -360)
    gp = skia.Paint(AntiAlias=True); gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)); gp.setAlphaf(0.5)
    c.save(); c.translate(640, 360); c.scale(s, s)
    r = skia.Rect.MakeXYWH(-img.width() / 2, -img.height() / 2, img.width(), img.height())
    c.drawImageRect(img, r, SAMPLING, gp); c.drawImageRect(img, r, SAMPLING, skia.Paint(AntiAlias=True))
    c.restore(); c.restore()
    dust(c, T, seed=31, n=70, col_=GOLD, a=0.5, size=1.0)

# ---------- l'amphore de Dédale : méandres -> labyrinthe (Hilbert) -> Discobole -> disque ----------
def d2xy(n, d):
    x = y = 0; t = d; s = 1
    while s < n:
        rx = 1 & (t // 2); ry = 1 & (t ^ rx)
        if ry == 0:
            if rx == 1: x, y = s - 1 - x, s - 1 - y
            x, y = y, x
        x += s * rx; y += s * ry; t //= 4; s *= 2
    return x, y

@functools.lru_cache(maxsize=4)
def hilbert(order=5):
    n = 2 ** order
    return np.array([d2xy(n, i) for i in range(n * n)], np.float32) / (n - 1), n

AMP = dict(cx=640, top=110, bot=640)
def amp_halfw(v):
    """Demi-largeur de la panse selon v (0 = haut du col, 1 = pied)."""
    neck = 0.13 + 0.0 * v
    body = 0.48 * math.sin(math.pi * clamp((v - 0.12) / 0.86)) ** 0.8
    w = max(neck if v < 0.2 else 0.0, body) if v > 0.08 else 0.14
    if v > 0.93: w = 0.16
    return w * 330

def amphora_outline():
    ys = np.linspace(0, 1, 120); L = []; R = []
    for v in ys:
        y = AMP["top"] + v * (AMP["bot"] - AMP["top"]); hw = amp_halfw(v)
        L.append((AMP["cx"] - hw, y)); R.append((AMP["cx"] + hw, y))
    return L + R[::-1]

def hilbert_on_amphora():
    pts, n = hilbert(5)
    out = []
    for u, v in pts:
        vv = 0.1 + 0.85 * v; hw = amp_halfw(vv)
        x = AMP["cx"] + hw * math.sin(math.pi / 2 * (2 * u - 1)) * 0.94
        y = AMP["top"] + vv * (AMP["bot"] - AMP["top"])
        out.append((x, y))
    return out

@functools.lru_cache(maxsize=1)
def disco_contour_world():
    """Contour du Discobole (asset disco_marble) dans le repère de l'écran, centré sur l'amphore."""
    c = np.load(f"{ROOT}/assets/eng/disco_contour.npy").astype(np.float32)
    img = asset("disco_marble"); s = 540 / img.height()
    xy = (c - np.array([img.width() / 2, img.height() / 2])) * s + np.array([640, 375])
    return xy, s

def s_amphora(c, lt, d, T, p):
    u = lt / d
    hil = hilbert_on_amphora()
    # phase a-b : zoom arrière depuis les méandres (x8) jusqu'à l'amphore entière
    zoom = math.exp(lerp(math.log(8.0), 0.0, ease_io(clamp(u / 0.48))))
    focus = (lerp(560, 640, ease_io(clamp(u / 0.48))), lerp(420, 375, ease_io(clamp(u / 0.48))))
    fade = 1 - smooth((u - 0.50) / 0.20)                   # l'amphore s'efface
    c.drawRect(skia.Rect(0, 0, W, H), fill_paint((222, 196, 150)))
    paper_bg(c, (226, 204, 160))
    c.save(); camera(c, zoom * (1 + 0.6 * ease_in(clamp((u - 0.80) / 0.20), 2)), *(focus if u < 0.8 else disc_pos()))
    if fade > 0:
        c.saveLayerAlpha(None, int(255 * fade))
        outline = path_from(amphora_outline(), True)
        c.drawPath(outline, fill_paint(TERRA))
        hatch_path(c, outline, 3.0, INK, 0.18)
        c.save(); c.clipPath(outline, doAntiAlias=True)
        c.drawPath(path_from(hil), stroke_paint(INK, 5.2, 1.0, skia.Paint.kSquare_Cap))
        c.restore()
        c.drawPath(outline, stroke_paint(INK, 2.5))
        # anses
        for sgn in (-1, 1):
            h = skia.Path(); x0 = AMP["cx"] + sgn * 50; h.moveTo(x0, 150); h.cubicTo(x0 + sgn * 130, 120, x0 + sgn * 150, 230, AMP["cx"] + sgn * 140, 260)
            c.drawPath(h, stroke_paint(INK, 9))
        c.restore()
        # la ligne d'or court dans le labyrinthe (fenêtre glissante + traînée)
        k = ease_io(clamp(u / 0.55)); n = len(hil); i1 = int(k * (n - 1)); i0 = max(0, i1 - 90)
        if i1 > 1: gold_line(c, hil[i0:i1 + 1], 1.0, 2.2 / max(1, zoom * 0.5), T, head=False, energy_=0.4)
        if u < 0.55: glow(c, *hil[i1], 30 / max(1, zoom * 0.4), GOLD, 0.9)
    # phase c : la ligne d'or trace le Discobole, qui apparaît gravé
    if u > 0.45:
        xy, s = disco_contour_world()
        kk = ease_io(clamp((u - 0.45) / 0.33))
        a_img = smooth((u - 0.62) / 0.16)
        if a_img > 0: draw_img(c, asset("disco_marble"), 640, 375, s, alpha=a_img)
        gold_line(c, xy.tolist() + [xy[0].tolist()], kk, 2.2, T, head=kk < 1, energy_=0.5)
    # phase d : plongée vers le disque qui s'embrase
    if u > 0.78:
        x, y = disc_pos(); k = clamp((u - 0.78) / 0.22)
        glow(c, x, y, 40 + 140 * k, GOLD, 0.9 * k)
        c.drawCircle(x, y, 26, fill_paint(mix((240, 230, 210), GOLD, k), k))
    c.restore()
    flash(c, 0.6 * ease_in(clamp((u - 0.93) / 0.07), 2), (255, 230, 170))

@functools.lru_cache(maxsize=1)
def disc_pos():
    """Le disque : point le plus haut-gauche du contour du Discobole (dans sa main levée)."""
    xy, s = disco_contour_world()
    k = np.argmin(xy[:, 0] + xy[:, 1])
    return float(xy[k, 0] + 18), float(xy[k, 1] + 18)

# ---------- le disque devenu soleil se lève ----------
def s_sunrise(c, lt, d, T, p):
    k = ease_out(lt / d)
    c.save(); camera(c, 1.0 + 0.04 * lt / d)
    sky(c, (250, 214, 150), OCHRE_LO, 0, 520, horizon=460)
    y = lerp(560, 330, k)
    glow(c, 640, y, 360, (255, 220, 160), 0.5)
    engraved_sun(c, 640, y, 150, breathe=0.02 * pulse(T))
    hills(c, [dict(L, col=mix(L["col"], (60, 30, 20), 0.35)) for L in HOOK_HILLS], dx=-20 * lt)
    c.drawRect(skia.Rect(-10, GROUND, W + 10, H + 10), fill_paint((90, 50, 30)))
    c.restore()

# ---------- David en contre-plongée ----------
def s_david(c, lt, d, T, p):
    vgrad(c, skia.Rect(0, 0, W, H), [(58, 48, 40), (30, 24, 20)])
    vault = asset("david_vault"); marble = asset("david_marble")
    x0, y0, sm = np.load(f"{ROOT}/assets/eng/david_marble_geo.npy")
    sv = vault.width() / 1920.0                       # vault = photo entière réduite à 1300 px
    k = ease_io(lt / d)
    S = 1.02 * W / vault.width() * lerp(1.0, 1.08, k)
    c.save(); c.translate(640, lerp(430, 470, k)); c.scale(S, S); c.translate(-vault.width() / 2, -vault.height() * 0.28)
    c.drawImage(vault, 0, 0, SAMPLING, skia.Paint(AntiAlias=True, Alphaf=0.55))
    c.translate(x0 * sv, y0 * sv); c.scale(sv / sm, sv / sm)
    p_ = skia.Paint(AntiAlias=True); p_.setImageFilter(skia.ImageFilters.DropShadowOnly(10, 10, 12, 12, col(INK, 0.5)))
    c.drawImage(marble, 0, 0, SAMPLING, p_); c.drawImage(marble, 0, 0, SAMPLING, skia.Paint(AntiAlias=True))
    c.restore()
    vignette(c, 0.55)

# ---------- la Création : les deux index, étincelle sur le temps ----------
def s_creation(c, lt, d, T, p):
    """Repère commun : l'image source (1400 px de large) réduite à la largeur de l'écran. geo = (x0, y0, s) :
    pixel d'asset (ax, ay) <-> source (x0 + ax/s, y0 + ay/s)."""
    c.drawRect(skia.Rect(0, 0, W, H), fill_paint((58, 52, 46)))
    pa = skia.Path(); pa.addRect(skia.Rect(0, 0, W, H)); hatch_path(c, pa, 4.0, (20, 16, 12), 0.35)
    k = ease_io(lt / d); gap = 35 * (1 - k)
    S = W / 1400
    sx, sy = spark_pos()
    c.save(); camera(c, 1.3 + 0.08 * k, sx, sy)
    for name, sgn in (("creation_adam", -1), ("creation_god", 1)):
        x0, y0, s_ = np.load(f"{ROOT}/assets/eng/{name}_geo.npy")
        shadowed(c, asset(name), x0 * S + sgn * gap, y0 * S, S / s_, off=(8, 10), blur=10, a=0.4, anchor=(0, 0))
    pu = pulse(T, 0.14)
    glow(c, sx, sy, 50 + 80 * pu, GOLD, 0.6 + 0.4 * pu)
    c.drawCircle(sx, sy, 3 + 3 * pu, fill_paint((255, 250, 230)))
    c.restore()

@functools.lru_cache(maxsize=1)
def spark_pos():
    S = W / 1400; out = []
    for name, side in (("creation_adam", "right"), ("creation_god", "left")):
        x0, y0, s_ = np.load(f"{ROOT}/assets/eng/{name}_geo.npy")
        fx, fy, _, _ = alpha_extent(name, 0, 1, side)
        out.append(((x0 + fx / s_) * S, (y0 + fy / s_) * S))
    return (out[0][0] + out[1][0]) / 2, (out[0][1] + out[1][1]) / 2

# ---------- Atlas porte la sphère céleste ----------
@functools.lru_cache(maxsize=1)
def constellations(seed=3):
    rng = np.random.default_rng(seed); out = []
    for k in range(9):
        lon = rng.uniform(0, 2 * math.pi); lat = rng.uniform(-1.0, 1.0); pts = []
        for j in range(rng.integers(3, 7)):
            lon += rng.normal(0, 0.18); lat += rng.normal(0, 0.14); pts.append((lon, lat))
        out.append(pts)
    return out

def celestial_sphere(c, x, y, r, rot, a=1.0, T=0.0):
    """Sphère céleste d'or : méridiens, parallèles, écliptique inclinée de 23°, constellations dont les étoiles luisent."""
    def proj(lon, lat, tilt=0.0):
        X = math.cos(lat) * math.sin(lon + rot); Y = -math.sin(lat); Z = math.cos(lat) * math.cos(lon + rot)
        if tilt:
            ca, sa = math.cos(tilt), math.sin(tilt); X, Y = X * ca - Y * sa, X * sa + Y * ca
        return x + r * X, y + r * Y, Z
    lp = stroke_paint((255, 214, 120), 2.6, a); bp = stroke_paint(GOLD, 1.0, 0.3 * a)
    for m in range(12):
        lon = m * math.pi / 6
        pts = [proj(lon, la) for la in np.linspace(-math.pi / 2, math.pi / 2, 40)]
        for (x1, y1, z1), (x2, y2, z2) in zip(pts, pts[1:]): c.drawLine(x1, y1, x2, y2, lp if z1 > 0 else bp)
    for la in (-60, -30, 0, 30, 60):
        pts = [proj(lo, math.radians(la)) for lo in np.linspace(0, 2 * math.pi, 60)]
        for (x1, y1, z1), (x2, y2, z2) in zip(pts, pts[1:]): c.drawLine(x1, y1, x2, y2, lp if z1 > 0 else bp)
    pts = [proj(lo, 0, math.radians(23)) for lo in np.linspace(0, 2 * math.pi, 80)]
    for (x1, y1, z1), (x2, y2, z2) in zip(pts, pts[1:]): c.drawLine(x1, y1, x2, y2, stroke_paint(FIRE, 2.2, 0.9 * a) if z1 > 0 else bp)
    for k, con in enumerate(constellations()):
        P = [proj(lo, la) for lo, la in con]
        for (x1, y1, z1), (x2, y2, z2) in zip(P, P[1:]):
            if z1 > 0 and z2 > 0: c.drawLine(x1, y1, x2, y2, stroke_paint((255, 240, 200), 1.0, 0.7 * a))
        for j, (px, py, pz) in enumerate(P):
            if pz > 0: c.drawCircle(px, py, 2.5 + 1.5 * math.sin(T * 3 + k + j), fill_paint((255, 248, 225), a))
    c.drawCircle(x, y, r, stroke_paint(GOLD, 2.2, a))

def s_atlas(c, lt, d, T, p):
    vgrad(c, skia.Rect(0, 0, W, H), [NIGHT, (30, 32, 48)])
    stars(c, T, seed=7, a=0.8, dx=-10 * lt)
    img = asset("atlas_marble"); gx, gy, gr = np.load(f"{ROOT}/assets/eng/atlas_globe.npy")
    k = ease_io(lt / d); s = 660 / img.height() * lerp(1.0, 1.05, k)
    cx, cy = 640, 360 + 25 * k
    c.save(); c.translate(cx, cy); c.scale(s, s); c.translate(-img.width() / 2, -img.height() / 2)
    glow(c, gx, gy, gr * 1.8, GOLD, 0.25)
    p_ = skia.Paint(AntiAlias=True); p_.setImageFilter(skia.ImageFilters.DropShadowOnly(12, 12, 14, 14, col(INK, 0.6)))
    c.drawImage(img, 0, 0, SAMPLING, p_); c.drawImage(img, 0, 0, SAMPLING, skia.Paint(AntiAlias=True))
    gl = skia.Paint(); c.saveLayer(None, None)
    celestial_sphere(c, gx, gy, gr * 1.04, rot=0.4 * T, T=T)
    c.restore()
    c.restore()
    # hommes minuscules aux pieds d'Atlas
    for i, x in enumerate((360, 420, 470, 820, 870, 930)):
        place(c, "runner_torch_sil", x, 712, 60 + 6 * (i % 3), flip=x > 640, a=0.2)

# ---------- la foudre sur les colonnes ----------
def s_lightning(c, lt, d, T, p):
    t_hit = 0.08
    f = 1.0 if lt < t_hit + 0.05 else 0.0
    vgrad(c, skia.Rect(0, 0, W, H), [(22, 24, 38), (46, 48, 70)])
    img = asset("parthenon"); s = W * 1.08 / img.width()
    c.save(); camera(c, 1.0 + 0.05 * lt / d, 640, 360)
    draw_img(c, img, 640, 440, s)
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color4f=col((40, 44, 80), 0.55), BlendMode=skia.BlendMode.kMultiply))
    prog = ease_out(clamp((lt - 0.0) / 0.12))
    a = clamp(1.2 - (lt - 0.12) / 0.5)
    draw_lightning(c, 700, -20, prog, seed=2, scale=1.0, a=a)
    if lt > d * 0.5: draw_lightning(c, 420, -20, ease_out(clamp((lt - d * 0.5) / 0.1)), seed=5, scale=0.7, a=clamp(1.2 - (lt - d * 0.5) / 0.3))
    c.restore()
    flash(c, 0.55 * clamp(1 - lt / 0.12), (220, 225, 255))

# ---------- Prométhée gravit l'escalier en spirale ----------
def spiral_steps(cx, base, R, n=38, dh=16.0, a0=0.0, turns=2.3):
    steps = []
    for k in range(n):
        a = a0 + k / n * turns * 2 * math.pi
        steps.append((cx + R * math.cos(a), base - k * dh, math.sin(a), a))
    return steps

def draw_spiral(c, cx, base, R, T, n=38, dh=16.0, turns=2.3, col_=INK, light=(250, 230, 190), rot=0.0):
    steps = spiral_steps(cx, base, R, n, dh, rot, turns)
    # les marches de derrière d'abord (profondeur = sin(a))
    for x, y, z, a in sorted(steps, key=lambda s: s[2]):
        w = 70 * (0.75 + 0.25 * z); h = 10
        r = skia.Rect(x - w / 2, y - h, x + w / 2, y)
        c.drawRect(r, fill_paint(mix(col_, (90, 60, 40), 0.3 * (1 - z))))
        c.drawLine(x - w / 2, y - h, x + w / 2, y - h, stroke_paint(light, 1.2, 0.6 * (0.5 + 0.5 * z)))
    return steps

def s_stairs(c, lt, d, T, p):
    k = ease_io(lt / d)
    sky(c, (250, 214, 150), OCHRE_LO, 0, H, horizon=H)
    engraved_sun(c, 640, 80, 90)
    c.save(); camera(c, 1.0, 640, lerp(420, 300, k))
    c.drawRect(skia.Rect(630, 40, 650, 760), fill_paint(INK))          # le fût central
    steps = draw_spiral(c, 640, 720, 150, T, n=44, dh=15.0, turns=2.6)
    j = int(lerp(10, 26, k)); x, y, z, a = steps[j]
    place(c, "runner_torch_blackfig", x, y - 10, 90, flip=math.cos(a) > 0, a=0.3)
    flame(c, x + (-18 if math.cos(a) > 0 else 18), y - 92, 22, T, seed=3)
    c.restore()

# ---------- la torche tendue vers le soleil s'enflamme ----------
@functools.lru_cache(maxsize=1)
def torch_tip():
    x, y, w, h = alpha_extent("runner_torch_blackfig", 0, 0.45, "right"); return x, y, w, h

def s_torch_sun(c, lt, d, T, p):
    k = ease_io(lt / d)
    sky(c, (255, 226, 160), OCHRE_LO, 0, H, horizon=H)
    engraved_sun(c, 1180, 330, 330, breathe=0.02 * pulse(T))
    img = asset("runner_torch_blackfig"); s = fit_h(img, 620)
    tx, ty, iw, ih = torch_tip()
    target = (lerp(760, 850, k), 250)
    x = target[0] - (tx - iw / 2) * s; y = target[1] - (ty - ih / 2) * s
    shadowed(c, img, x, y, s, off=(10, 10), blur=10, a=0.35)
    t_ign = beat(p["b0"] + 1) - p["_t0"]
    if lt > t_ign:
        u = lt - t_ign
        flame(c, target[0] + 6, target[1] + 10, 40 + 90 * ease_out(u / 0.25), T, seed=8)
        sparks(c, target[0], target[1], T, 30, seed=2, spread=180)
        flash(c, 0.35 * clamp(1 - u / 0.1))

def s_torch_close(c, lt, d, T, p):
    dark_bg(c, (16, 10, 8))
    c.save(); camera(c, 1.0 + 0.1 * lt / d, 640, 360, rot=-3 + 3 * lt / d)
    st = skia.Path(); st.moveTo(560, 800); st.lineTo(690, 430); st.lineTo(722, 440); st.lineTo(600, 810); st.close()
    c.drawPath(st, fill_paint((60, 34, 20)))
    for k in range(6):
        y = 470 + k * 16; c.drawLine(670 - k * 6, y, 712 - k * 6, y + 10, stroke_paint((140, 80, 40), 3))
    flame(c, 700, 440, 330, T, seed=11)
    sparks(c, 700, 300, T, 60, seed=5, spread=320)
    c.restore()

# ---------- la statue : de profil, puis tournée vers le voleur (œil cerclé d'or) ----------
def s_statue(c, lt, d, T, p):
    dark_bg(c, (30, 24, 20), glow_c=(255, 220, 170), gx=900, gy=360, gr=700, ga=0.08)
    img = asset("antinous_marble")
    turned = T >= beat(p["b0"] + 1)
    if not turned:
        c.save(); camera(c, 1.0 + 0.03 * lt / d)
        shadowed(c, img, 700, 400, fit_h(img, 760), flip=True, off=(10, 10), blur=12, a=0.45)
        c.restore()
    else:
        u = T - beat(p["b0"] + 1)
        s = fit_h(img, 1100) * (1 + 0.03 * u)
        ex, ey = 0.81 * img.width(), 0.53 * img.height()
        x = 700 - (ex - img.width() / 2) * s + 180; y = 330 - (ey - img.height() / 2) * s
        shadowed(c, img, x, y, s, off=(10, 10), blur=12, a=0.45)
        # l'œil cerclé d'un fin trait d'or (pas de halo)
        exs, eys = x + (ex - img.width() / 2) * s, y + (ey - img.height() / 2) * s
        pa = skia.Path(); pa.addArc(skia.Rect(exs - 34, eys - 16, exs + 34, eys + 16), 180, 360 * ease_out(u / 0.25))
        c.drawPath(pa, stroke_paint(GOLD, 2.4))

# ---------- la descente avec la flamme (escalier vu de dessus) ----------
def s_descent(c, lt, d, T, p):
    k = ease_io(lt / d)
    vgrad(c, skia.Rect(0, 0, W, H), [(22, 22, 34), (10, 10, 16)])
    c.save(); camera(c, lerp(1.0, 1.25, k), 640, 360, rot=-20 * k)
    pts = []
    for i in range(70):
        a = i / 70 * 3.2 * 2 * math.pi; r = lerp(330, 40, i / 70)
        x0, y0 = 640 + r * math.cos(a), 360 + r * math.sin(a)
        x1, y1 = 640 + (r - 34) * math.cos(a), 360 + (r - 34) * math.sin(a)
        c.drawLine(x0, y0, x1, y1, stroke_paint((120, 110, 130), 5, 0.7))
        pts.append(((x0 + x1) / 2, (y0 + y1) / 2))
    c.drawCircle(640, 360, 22, fill_paint(INK))
    head = gold_line(c, pts, k, 2.4, T, energy_=0.6)
    flame(c, float(head[0]), float(head[1]), 28, T, seed=12, glow_=False)
    c.restore()

# ---------- les Anunnaki ----------
def s_seal(c, lt, d, T, p):
    """Le sceau-cylindre roule de gauche à droite ; l'empreinte apparaît (Utu se lève entre les montagnes)."""
    k = ease_io(lt / d)
    c.drawRect(skia.Rect(0, 0, W, H), fill_paint((120, 56, 30)))
    pa = skia.Path(); pa.addRect(skia.Rect(0, 0, W, H)); hatch_path(c, pa, 3.2, INK, 0.3)
    img = asset("anu_adda_seal_gold"); s = 1180 / img.width()
    w = img.width() * s; h = img.height() * s; x0 = 640 - w / 2; y0 = 380 - h / 2
    xr = x0 + w * k
    c.save(); camera(c, 1.0 + 0.05 * k, lerp(500, 700, k), 380)
    c.save(); c.clipRect(skia.Rect(x0, y0 - 10, xr, y0 + h + 10), doAntiAlias=True)
    draw_img(c, img, 640, 380, s)
    c.restore()
    # le cylindre (pierre sombre) qui roule sur la bordure
    cyl = skia.Rect(xr - 40, y0 - 30, xr + 40, y0 + h + 30)
    sh = skia.GradientShader.MakeLinear([skia.Point(xr - 40, 0), skia.Point(xr + 40, 0)], [col((30, 26, 30)), col((110, 100, 110)), col((20, 18, 20))], None)
    c.drawRoundRect(cyl, 14, 14, skia.Paint(AntiAlias=True, Shader=sh))
    for j in range(12):
        yy = y0 - 20 + ((j * 30 + k * 600) % (h + 40))
        c.drawLine(xr - 36, yy, xr + 36, yy, stroke_paint((200, 170, 110), 1.5, 0.5))
    c.restore()

@functools.lru_cache(maxsize=1)
def shamash_disk():
    img = asset("anu_shamash_gold"); return 0.47 * img.width(), 0.70 * img.height(), 0.075 * img.width()

def wings(c, x, y, span, T, col_=GOLD):
    for sgn in (-1, 1):
        for k in range(9):
            L = span * (1 - k * 0.08); a = math.radians(-8 + k * 5 + 3 * math.sin(T * 2))
            pa = skia.Path(); pa.moveTo(x + sgn * 40, y + k * 5)
            pa.quadTo(x + sgn * L * 0.6, y - 20 + k * 6, x + sgn * L, y + k * 9 - 10)
            c.drawPath(pa, stroke_paint(col_, 3.0 - k * 0.2, 0.9))

def s_anu_descent(c, lt, d, T, p):
    k = ease_io(lt / d)
    vgrad(c, skia.Rect(0, 0, W, H), [NIGHT, (40, 30, 40)])
    stars(c, T, seed=9, a=0.8)
    y = lerp(-60, 250, k)
    for j in range(14):
        a = math.radians(70 + j * 3); c.drawLine(640, y, 640 + 900 * math.cos(a) * (1 if j % 2 else -1), y + 900 * math.sin(a), stroke_paint(GOLD, 2, 0.07))
    glow(c, 640, y, 260, GOLD, 0.35)
    wings(c, 640, y, 330, T)
    img = asset("anu_shamash_gold"); dx, dy, dr = shamash_disk(); R = 95
    c.save(); pth = skia.Path(); pth.addCircle(640, y, R); c.clipPath(pth, doAntiAlias=True)
    c.drawRect(skia.Rect(0, 0, W, H), fill_paint(INK))
    s = R / dr; draw_img(c, img, 640 - (dx - img.width() / 2) * s, y - (dy - img.height() / 2) * s, s)
    c.restore(); c.drawCircle(640, y, R, stroke_paint(GOLD, 3))
    # la plaine et les hommes d'argile qui attendent (figures noires, variations)
    c.drawRect(skia.Rect(-10, 600, W + 10, H + 10), fill_paint((24, 18, 20)))
    for i, x in enumerate(np.linspace(180, 1100, 9)):
        place(c, "durer_adam", float(x), 606, 120 + 14 * ((i * 7) % 3), flip=x > 640, a=0.2)

def s_apkallu(c, lt, d, T, p):
    dark_bg(c, (12, 9, 7))
    img = asset("anu_apkallu_gold"); s = fit_h(img, 760)
    cone = (0.80 * img.width(), 0.27 * img.height())
    k = ease_io(lt / d)
    c.save(); camera(c, lerp(1.0, 1.35, k), lerp(640, 640 + (cone[0] - img.width() / 2) * s, k), lerp(360, 360 + (cone[1] - img.height() / 2) * s, k))
    draw_img(c, img, 640, 360, s)
    cx, cy = 640 + (cone[0] - img.width() / 2) * s, 360 + (cone[1] - img.height() / 2) * s
    t_ign = beat(p["b0"] + 1) - p["_t0"]
    if lt > t_ign:
        u = lt - t_ign
        flame(c, cx, cy, 30 + 50 * ease_out(u / 0.2), T, seed=13)
        flash(c, 0.25 * clamp(1 - u / 0.1))
    c.restore()

# ---------- deux torches se passent la flamme ----------
def torch_stick(c, x0, y0, x1, y1):
    c.drawLine(x0, y0, x1, y1, stroke_paint((60, 34, 20), 18))
    for k in range(5):
        u = 0.05 + k * 0.05; x = lerp(x1, x0, u); y = lerp(y1, y0, u)
        c.drawCircle(x, y, 11, stroke_paint((150, 90, 40), 2.5))

def s_torches(c, lt, d, T, p):
    dark_bg(c, (14, 10, 8), glow_c=FIRE, ga=0.08)
    k = ease_io(clamp(lt / (d * 0.4)))
    tipL = (lerp(420, 610, k), lerp(520, 330, k)); tipR = (lerp(860, 670, k), lerp(520, 330, k))
    c.save(); camera(c, 1.0 + 0.06 * lt / d, 640, 360)
    torch_stick(c, 180, 900, *tipL); torch_stick(c, 1100, 900, *tipR)
    flame(c, tipL[0], tipL[1], 120, T, seed=14)
    t_pass = beat(p["b0"] + 2) - p["_t0"]
    if lt > t_pass:
        u = lt - t_pass
        # arc d'étincelles qui passe d'une torche à l'autre, puis la seconde s'embrase
        for j in range(20):
            f = clamp(u / 0.15 - j * 0.02); x = lerp(tipL[0], tipR[0], f); y = lerp(tipL[1], tipR[1], f) - 40 * math.sin(math.pi * f)
            c.drawCircle(x, y, 2.5, fill_paint((255, 220, 140), 1 - j / 20))
        flame(c, tipR[0], tipR[1], 120 * ease_out(clamp((u - 0.1) / 0.25)), T, seed=15)
    sparks(c, 640, 330, T, 30, seed=6, spread=200)
    c.restore()

# ---------- la bascule des figures noires en figures rouges ----------
def s_flip(c, lt, d, T, p):
    t_flip = beat(p["b0"] + 3) - p["_t0"]
    red = lt >= t_flip
    bg = INK if red else TERRA; band = TERRA if red else INK
    c.drawRect(skia.Rect(0, 0, W, H), fill_paint(bg))
    c.save(); camera(c, 1.0 + 0.07 * lt / d, 640, 380)
    meander_band(c, 70, 44, band, x_off=40 * T); meander_band(c, 610, 44, band, x_off=-40 * T)
    img = asset("disco_redfig" if red else "disco_blackfig"); s = fit_h(img, 500)
    if red:
        u = lt - t_flip
        glow(c, 640, 380, 420, FIRE, 0.35 * clamp(1 - u / 0.6) + 0.1)
    draw_img(c, img, 640, 380, s)
    if not red:
        # la flamme approche de la gauche
        fx = lerp(-60, 330, ease_io(clamp(lt / t_flip)))
        flame(c, fx, 420, 70, T, seed=16)
    c.restore()
    if red: flash(c, 0.5 * clamp(1 - (lt - t_flip) / 0.12), (255, 200, 150))
