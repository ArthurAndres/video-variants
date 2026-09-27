"""Plans 0:00-0:19,65 : le hook (l'enfant, la ligne), Éden, les symboles, la tache d'encre, la graine.
Signature : fn(c, lt, d, T, p) — lt temps local, d durée du plan, T temps absolu, p paramètres du plan."""
import math
import numpy as np, skia, cv2
from engine.core import *
from engine.common import *

GROUND = 520

def fit_h(img, h): return h / img.height()

@functools.lru_cache(maxsize=32)
def alpha_extent(name, y0=0.0, y1=1.0, side="left"):
    """Point extrême (gauche/droite/haut) de la partie opaque d'un asset, en coordonnées image (pour poser un fruit dans une main)."""
    a = cv2.imread(f"{ROOT}/assets/eng/{name}.png", cv2.IMREAD_UNCHANGED)[..., 3] > 128
    h = a.shape[0]; sub = a[int(y0 * h):int(y1 * h)]
    ys, xs = np.where(sub)
    if side == "left": i = np.argmin(xs)
    elif side == "right": i = np.argmax(xs)
    else: i = np.argmin(ys)
    return float(xs[i]), float(ys[i] + int(y0 * h)), a.shape[1], a.shape[0]

# ---------- décor du hook : monde ocre (collines, soleil, herbe) ----------
HOOK_HILLS = [dict(y=430, amp=40, seed=11, col=(226, 170, 100), par=0.3, step=3.2, a=0.22),
              dict(y=470, amp=34, seed=12, col=(200, 130, 70), par=0.6, step=3.0, a=0.28),
              dict(y=505, amp=18, seed=13, col=(150, 90, 50), par=1.0, step=2.8, a=0.35, cross=True)]

def ochre_world(c, t, dx=0.0, sun=(820, 330, 110), ground=GROUND, grass_=True, sky_=(OCHRE_HI, OCHRE_LO)):
    sky(c, sky_[0], sky_[1], 0, ground, horizon=ground - 60)
    engraved_sun(c, sun[0] + dx * 0.1, sun[1], sun[2], breathe=0.01 * pulse(t))
    tops = hills(c, HOOK_HILLS, dx)
    # terre au premier plan : sombre, hachures croisées
    gp = skia.Path(); gp.addRect(skia.Rect(-10, ground, W + 10, H + 10))
    c.drawRect(skia.Rect(-10, ground, W + 10, H + 10), fill_paint((110, 62, 34)))
    hatch_path(c, gp, 2.8, INK, 0.45, 0.7, cross=True)
    c.drawLine(-10, ground, W + 10, ground, stroke_paint(INK, 1.6))
    if grass_: grass(c, ground + 1, -20 + (dx % 40) - 40, W + 20, seed=5, h=11, a=0.85)
    return tops

def blank_side(c, x_front, tops, seed, ground=GROUND):
    """Côté papier vierge : papier + esquisse au crayon du même monde."""
    c.save()
    edge = torn_edge(x_front, seed)
    p = skia.Path(); p.moveTo(W + 10, -20)
    for x, y in edge: p.lineTo(x, y)
    p.lineTo(W + 10, H + 20); p.close(); c.clipPath(p, doAntiAlias=True)
    paper_bg(c)
    pencil_lines(c, tops + [[(-10, ground), (W + 10, ground)]], 0.35)
    c.restore()
    # bord déchiré : fine ombre + liseré
    c.drawPath(path_from(edge), stroke_paint(INK, 1.2, 0.55))
    return edge

def frontier_world(c, t, x_front, seed, dx=0.0, sun=(820, 330, 110), ground=GROUND, point=True, energy_=0.5):
    tops = ochre_world(c, t, dx, sun, ground)
    edge = blank_side(c, x_front, tops, seed, ground)
    if point:
        # le point de lumière dorée qui trace la ligne du sol, sur la frontière
        yline = ground
        glow(c, x_front, yline, 60, GOLD, 0.9); c.drawCircle(x_front, yline, 3.5, fill_paint((255, 246, 220)))
        c.drawLine(x_front - 200, yline, x_front, yline, stroke_paint(GOLD, 2.4, 0.9))

# ---------- 1. la goutte ----------
def s_drop(c, lt, d, T, p):
    paper_bg(c)
    t_imp = beat(0) - p["_t0"]
    c.save(); camera(c, 1.0 + 0.05 * lt / d, 640, 380)
    if lt < t_imp:
        y = lerp(-60, 380, ease_in(lt / t_imp, 2)); drop(c, 640, y, 7, 2.2)
    else:
        k = ease_out((lt - t_imp) / 0.14, 3)
        ink_splash(c, 640, 380, 8 + 18 * k, seed=4, lobes=26, droplets=14, prog=k)
    c.restore()

# ---------- 2. le point devient soleil, l'horizon se trace ----------
def s_sun_horizon(c, lt, d, T, p):
    paper_bg(c)
    k = ease_out(lt / (d * 0.55), 3)
    # le point devient soleil ; l'horizon est tracé de gauche à droite et le monde se colore derrière (frontière déchirée)
    xf = lerp(-20, 560, ease_io(lt / d))
    c.save(); world_clip(c, xf, seed=61)
    sky(c, OCHRE_HI, OCHRE_LO, 0, 470, horizon=410)
    c.drawRect(skia.Rect(-10, 470, W, H), fill_paint((150, 90, 50)))
    c.restore()
    c.drawPath(path_from(torn_edge(xf, 61)), stroke_paint(INK, 1.2, 0.5))
    engraved_sun(c, 640, lerp(380, 300, k), lerp(9, 80, k), rings=int(1 + 6 * k), alpha=1.0)
    gold_line(c, [(-20, 470), (1300, 470)], (xf + 20) / 1320, 2.2, T, energy_=0.4)

# ---------- 3. le pied figé à l'appui (macro) ----------
def s_foot(c, lt, d, T, p):
    c.save(); camera(c, 1.0 + 0.04 * lt / d, 640, 400, dx=-30 * lt / d)
    ochre_world(c, T, dx=-40 * lt / d, sun=(1000, 250, 160), ground=560)
    img = asset("foot_masaccio"); s = fit_h(img, 360)
    shadowed(c, img, 520, 566, s, off=(10, 4), blur=8, a=0.35, anchor=(0.5, 1.0))
    # poussière suspendue en trame (points)
    rng = np.random.default_rng(7)
    for i in range(140):
        x = 520 + rng.normal(0, 160); y = 560 - abs(rng.normal(0, 60))
        c.drawCircle(x + 6 * lt, y - 4 * lt, rng.uniform(1, 3.2), fill_paint((120, 70, 40), 0.55))
    c.restore()
    blank_side(c, lerp(1090, 1150, lt / d), [], 21, 560)

# ---------- 4. la ligne du sol se dessine (macro) ----------
def s_line_macro(c, lt, d, T, p):
    xf = lerp(520, 760, ease_io(lt / d))
    c.save(); camera(c, 1.7, xf, GROUND - 40)
    frontier_world(c, T, xf, 31, dx=0, sun=(900, 300, 110))
    c.restore()

# ---------- 5. profil de l'enfant, caméra qui avance ----------
def s_child_profile(c, lt, d, T, p):
    c.save(); camera(c, 1.0 + 0.08 * ease_out(lt / d), 600, 380)
    ochre_world(c, T, dx=-30 * lt / d, sun=(820, 300, 170))
    img = asset("child_profile"); s = fit_h(img, 560)
    shadowed(c, img, 560, 745, s, off=(-10, 8), blur=10, a=0.4, flip=True, anchor=(0.5, 1.0))
    dust(c, T, seed=2, n=50, a=0.5)
    c.restore()

# ---------- 6. le point de lumière qui trace (plan moyen) ----------
def s_point_medium(c, lt, d, T, p):
    xf = lerp(300, 840, ease_io(lt / d))
    c.save(); camera(c, 1.0, 640, 360, dx=-20 * lt / d)
    frontier_world(c, T, xf, 41, dx=-60 * lt / d)
    c.restore()

# ---------- 7. plan large : l'enfant suspendu en pleine foulée, le monde se colore ----------
def s_wide_child(c, lt, d, T, p):
    xf = lerp(760, 1060, ease_io(lt / d))
    dx = -90 * lt / d
    frontier_world(c, T, xf, 51, dx=dx, sun=(900, 380, 90))
    img = asset("child_back"); s = fit_h(img, 190)
    # ombre au sol (l'enfant est suspendu : ombre détachée)
    c.drawOval(skia.Rect(600, GROUND + 2, 700, GROUND + 12), fill_paint(INK, 0.35))
    shadowed(c, img, 650, GROUND - 8, s, off=(4, 3), blur=3, a=0.3, anchor=(0.5, 1.0))
    dust(c, T, seed=3, n=40, a=0.5, box=(0, 300, W, GROUND))

# ---------- 8. la ligne dessine le tronc de l'arbre d'Éden ----------
def s_trunk(c, lt, d, T, p):
    k = ease_io(lt / d)
    c.save(); camera(c, lerp(2.2, 1.6, k), 640, lerp(GROUND - 40, GROUND - 120, k))
    ochre_world(c, T, sun=(820, 260, 120))
    ytop = lerp(GROUND, GROUND - 130, clamp(k * 1.6))
    c.drawLine(640, GROUND, 640, ytop, stroke_paint(INK, lerp(2.4, 9, clamp(k * 1.4))))
    gold_line(c, [(640, GROUND), (640, GROUND - 130)], clamp(k * 1.6), 2.4, T, energy_=0.5)
    if k > 0.55: draw_tree(c, 640, GROUND, 0.95, grow=lerp(0.1, 0.45, (k - 0.55) / 0.45), seed=1, leaves=False)
    c.restore()

# ---------- Éden ----------
def eden(c, T, tree_scale=0.95, base=(640, GROUND), sun=(640, 300, 150), red=0.0, grow=1.0, sway=1.0, dx=0.0, ground=GROUND):
    top = mix(OCHRE_HI, RED_SKY1, red); bot = mix(OCHRE_LO, RED_SKY0, red)
    sky(c, top, bot, 0, ground, horizon=ground - 60)
    engraved_sun(c, sun[0], sun[1], sun[2], fill=mix((250, 232, 180), (225, 90, 50), red), breathe=0.012 * pulse(T))
    layers = [dict(L, col=mix(L["col"], (60, 18, 14), red)) for L in HOOK_HILLS]
    hills(c, layers, dx)
    c.drawRect(skia.Rect(-10, ground, W + 10, H + 10), fill_paint(mix((110, 62, 34), (40, 10, 8), red)))
    gp = skia.Path(); gp.addRect(skia.Rect(-10, ground, W + 10, H + 10)); hatch_path(c, gp, 2.8, INK, 0.45, 0.7, cross=True)
    c.drawLine(-10, ground, W + 10, ground, stroke_paint(INK, 1.6))
    grass(c, ground + 1, -20, W + 20, seed=8, h=10)
    draw_tree(c, base[0] + dx, base[1], tree_scale, grow, seed=1, sway=3.0 * sway, t=T)

def place(c, name, x, y_feet, height, flip=False, a=0.35):
    img = asset(name); s = fit_h(img, height)
    shadowed(c, img, x, y_feet, s, off=(6, 4), blur=4, a=a, flip=flip, anchor=(0.5, 1.0))

def s_couple(c, lt, d, T, p):
    c.save(); camera(c, 1.0 + 0.05 * lt / d, 640, 400)
    eden(c, T)
    place(c, "durer_adam", 420, GROUND + 6, 380)
    place(c, "durer_eve", 870, GROUND + 6, 370)
    dust(c, T, seed=9, n=50, col_=(255, 240, 200), a=0.6)
    c.restore()

def s_fruit_macro(c, lt, d, T, p):
    vgrad(c, skia.Rect(0, 0, W, H), [OCHRE_HI, OCHRE_LO])
    glow(c, 820, 200, 500, (255, 240, 200), 0.5)
    c.save(); camera(c, 1.0 + 0.06 * lt / d, 660, 380)
    # feuilles d'avant-plan floues (parallaxe)
    for k, (x, y, s) in enumerate([(160, 120, 5.0), (1150, 600, 6.0), (1000, 80, 4.0)]):
        c.save(); c.translate(x - 40 * lt, y); c.scale(s, s); c.rotate(30 * k)
        lf = skia.Path(); lf.moveTo(-40, 0); lf.quadTo(0, -20, 40, 0); lf.quadTo(0, 20, -40, 0)
        pp = fill_paint(INK, 0.85); pp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 2)); c.drawPath(lf, pp); c.restore()
    fruit(c, 660, 400, 150, bite=p.get("bite", 0.0), t=T)
    # goutte de rosée qui glisse
    c.drawCircle(600, 330 + 30 * lt / d, 7, fill_paint((255, 250, 240), 0.8))
    c.restore()

def reaching_hand(c, lt, d, T, red=0.0):
    """La main d'Adam (Michel-Ange, terre cuite gravée) se tend vers le fruit. Remplace le gros plan Dürer (3 échecs).
    Après la chute (red=1) : la main se tend vers une branche vide."""
    vgrad(c, skia.Rect(0, 0, W, H), [mix(OCHRE_HI, RED_SKY1, red), mix(OCHRE_LO, RED_SKY0, red)])
    glow(c, 900, 260, 420, (255, 235, 190), 0.35 * (1 - red))
    img = asset("creation_adam"); s = 1100 / img.width()
    fx, fy, iw, ih = alpha_extent("creation_adam", 0, 1, "right")
    reach = 40 * ease_out(lt / d)
    tip = (700 + reach, 400)
    x = tip[0] - (fx - iw / 2) * s; y = tip[1] - (fy - ih / 2) * s
    c.save(); camera(c, 1.0 + 0.05 * lt / d, 760, 380)
    br = skia.Path(); br.moveTo(1400, 120); br.quadTo(1100, 150, 930, 250); c.drawPath(br, stroke_paint(INK, 9))
    if red < 0.5:
        fruit(c, 900, 340, 62, t=T)
    shadowed(c, img, x, y, s, off=(8, 10), blur=8, a=0.35)
    c.restore()
    dust(c, T, seed=21, n=40, a=0.5)

def s_eve_hand(c, lt, d, T, p):
    reaching_hand(c, lt, d, T)

def s_adam_profile(c, lt, d, T, p):
    c.save(); camera(c, 1.0 + 0.06 * lt / d, 640, 360)
    sky(c, OCHRE_HI, OCHRE_LO, 0, H, horizon=H)
    engraved_sun(c, 820, 300, 200)
    img = asset("durer_adam"); s = fit_h(img, 2600)
    tx, ty, iw, ih = alpha_extent("durer_adam", 0, 1, "top")
    x = 600 - (tx - iw / 2) * s; y = 150 - (ty - ih / 2) * s
    shadowed(c, img, x, y, s, off=(8, 8), blur=8, a=0.35)
    dust(c, T, seed=12, n=40, a=0.6)
    c.restore()

def serpent_path(t, x0, y0, x1, y1, amp=18, waves=3.0, n=120, phase=0.0):
    pts = []
    for i in range(n):
        u = i / (n - 1); x = lerp(x0, x1, u); y = lerp(y0, y1, u)
        nx, ny = -(y1 - y0), (x1 - x0); L = math.hypot(nx, ny); nx /= L; ny /= L
        o = amp * math.sin(u * waves * 2 * math.pi + phase + t * 1.5) * (0.3 + 0.7 * u)
        pts.append((x + nx * o, y + ny * o))
    return pts

def draw_serpent(c, pts, width=16, head=True, eye=True, t=0.0, prog=1.0):
    """Le serpent = la ligne (épaisse, écailles en trame), tête et œil d'or."""
    part, hp, dv = polyline_partial(pts, prog)
    pa = path_from(part.tolist())
    c.drawPath(pa, stroke_paint(INK, width))
    # écailles : points clairs en trame le long du corps
    dp = stroke_paint((150, 110, 60), width * 0.28, 0.8); dp.setPathEffect(skia.DashPathEffect.Make([0.1, width * 0.45], 0))
    c.drawPath(pa, dp)
    if head:
        a = math.degrees(math.atan2(dv[1], dv[0]))
        c.save(); c.translate(float(hp[0]), float(hp[1])); c.rotate(a)
        hd = skia.Path(); hd.moveTo(-width * 0.3, -width * 0.7); hd.quadTo(width * 1.8, -width * 0.8, width * 2.2, 0); hd.quadTo(width * 1.8, width * 0.8, -width * 0.3, width * 0.7); hd.close()
        c.drawPath(hd, fill_paint(INK))
        if eye: c.drawCircle(width * 1.1, -width * 0.25, width * 0.2, fill_paint(GOLD))
        c.restore()

def s_serpent_hidden(c, lt, d, T, p):
    vgrad(c, skia.Rect(0, 0, W, H), [OCHRE_HI, OCHRE_LO])
    c.save(); camera(c, 1.0 + 0.05 * lt / d, 640, 360, dx=-30 * lt / d)
    draw_tree(c, 900, 1500, 3.2, 1.0, seed=1, sway=4, t=T)
    pts = serpent_path(T, 200, 330, 860, 250, amp=14, waves=2.2)
    draw_serpent(c, pts, 22, t=T)
    c.restore()
    # feuilles d'avant-plan (parallaxe plus rapide)
    draw_tree(c, 200 - 80 * lt / d, 1400, 4.5, 1.0, seed=7, sway=2, t=T)

def helix(cx, y_bot, y_top, rx, turns=3.0, n=240):
    pts = []
    for i in range(n):
        u = i / (n - 1); a = u * turns * 2 * math.pi
        pts.append((cx + rx * math.sin(a), lerp(y_bot, y_top, u) + rx * 0.25 * math.cos(a)))
    return pts

def s_couple_serpent(c, lt, d, T, p):
    c.save(); camera(c, 1.0, 640, 420, dy=10 * lt / d)
    eden(c, T, tree_scale=1.2, base=(640, 610), sun=(640, 260, 170), ground=610)
    place(c, "durer_adam", 360, 616, 470)
    place(c, "durer_eve", 930, 616, 460)
    pts = helix(640, 600, 420, 22, 2.5)
    draw_serpent(c, pts, 10, t=T, prog=ease_out(lt / d) * 0.9 + 0.1)
    c.restore()

def s_bite(c, lt, d, T, p):
    vgrad(c, skia.Rect(0, 0, W, H), [OCHRE_HI, OCHRE_LO])
    c.save(); camera(c, punch(lt, 0.08) * (1.05 + 0.04 * lt / d), 640, 380)
    b = ease_out(lt / 0.09)
    fruit(c, 640, 400, 170, bite=b, t=T)
    # jus qui gicle (gouttes rouges et or)
    rng = np.random.default_rng(3)
    if lt > 0.03:
        for i in range(34):
            a = rng.uniform(-1.3, 0.9); v = rng.uniform(150, 420); tt = lt - 0.03
            x = 640 + 170 * 0.9 + math.cos(a) * v * tt; y = 400 - 25 + math.sin(a) * v * tt + 500 * tt * tt
            c.drawCircle(x, y, rng.uniform(2, 6) * (1 - tt), fill_paint((200, 30, 20) if i % 3 else GOLD, 0.9))
    c.restore()

def s_moon(c, lt, d, T, p):
    k = ease_io(lt / d)
    vgrad(c, skia.Rect(0, 0, W, H), [mix(OCHRE_HI, RED_SKY0, k), mix(OCHRE_LO, RED_SKY1, k)])
    stars(c, T, seed=1, a=k * 0.8)
    x, y, r = 640, 360, 170
    body = skia.Path(); body.addCircle(x, y, r)
    bite = skia.Path(); br = lerp(0.42, 0.95, k) * r; bite.addCircle(x + lerp(0.92, 0.55, k) * r, y - lerp(0.15, 0.1, k) * r, br)
    moon = skia.Op(body, bite, skia.PathOp.kDifference_PathOp)
    c.drawPath(moon, fill_paint(mix((200, 40, 25), (245, 232, 200), k)))
    c.drawPath(moon, stroke_paint(INK, 2))
    glow(c, x - r * 0.4, y, r * 1.2, (255, 230, 190), 0.25 * k)

def red_world(c, T, sun=(640, 420, 190), ground=GROUND, dx=0.0):
    eden(c, T, sun=sun, red=1.0, grow=1.0, ground=ground, dx=dx, tree_scale=0.0001)

def s_couple_down(c, lt, d, T, p):
    c.save(); camera(c, 1.0 + 0.05 * lt / d, 640, 420)
    red_world(c, T, sun=(700, 440, 210))
    place(c, "masaccio_couple", 620 - 20 * lt / d, GROUND + 8, 470)
    c.restore()

def s_serpent_coiled(c, lt, d, T, p):
    c.save(); camera(c, 1.0 + 0.04 * lt / d, 700, 400, rot=-1.5 * lt / d)
    eden(c, T, tree_scale=1.5, base=(700, 700), sun=(520, 300, 150), red=1.0, ground=700)
    pts = helix(700, 690, 300, 30, 4.0)
    draw_serpent(c, pts, 14, t=T)
    c.restore()

def eye_shape(c, x, y, rw, rh, slit=1.0, t=0.0):
    e = skia.Path(); e.moveTo(x - rw, y); e.quadTo(x, y - rh * 2, x + rw, y); e.quadTo(x, y + rh * 2, x - rw, y); e.close()
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), rw, [col((255, 230, 140)), col(GOLD), col((150, 80, 20))], [0, 0.6, 1])
    c.drawPath(e, skia.Paint(AntiAlias=True, Shader=sh))
    c.save(); c.clipPath(e, doAntiAlias=True)
    for k in range(40):
        a = k / 40 * 2 * math.pi; c.drawLine(x, y, x + math.cos(a) * rw, y + math.sin(a) * rw, stroke_paint((120, 60, 10), 1, 0.35))
    if slit > 0:
        s = skia.Path(); s.addOval(skia.Rect(x - rw * 0.09 * slit, y - rh * 1.7, x + rw * 0.09 * slit, y + rh * 1.7)); c.drawPath(s, fill_paint(INK))
    c.restore(); c.drawPath(e, stroke_paint(INK, 3))

def scales_bg(c, col_=(40, 10, 8), a=1.0):
    c.drawRect(skia.Rect(0, 0, W, H), fill_paint(col_))
    p = stroke_paint((120, 40, 20), 1.2, 0.6 * a)
    for j in range(0, H + 40, 26):
        for i in range(-1, W // 30 + 2):
            x = i * 30 + (15 if (j // 26) % 2 else 0); pa = skia.Path(); pa.addArc(skia.Rect(x - 15, j - 15, x + 15, j + 15), 0, 180); c.drawPath(pa, p)

def s_serpent_eye(c, lt, d, T, p):
    c.save(); camera(c, 1.0 + 0.12 * ease_out(lt / d), 640, 360)
    scales_bg(c)
    eye_shape(c, 640, 360, 260, 70 * ease_out(lt / 0.2 + 0.2), 1.0, T)
    c.restore()

def s_red_sun(c, lt, d, T, p):
    k = ease_io(lt / (d * 0.7))
    vgrad(c, skia.Rect(0, 0, W, H), [RED_SKY0, RED_SKY1])
    if k < 1: eye_shape(c, 640, 360, lerp(260, 190, k), lerp(70, 95, k), 1 - k, T)
    engraved_sun(c, 640, 360, 190, fill=(225, 90, 50), alpha=k)
    hills(c, [dict(L, col=(40, 10, 8)) for L in HOOK_HILLS[1:]])

def gate(c, x, ground, h=360):
    for gx in (x - 120, x + 120):
        r = skia.Rect(gx - 26, ground - h, gx + 26, ground); c.drawRect(r, fill_paint(INK))
        pa = skia.Path(); pa.addRect(r); hatch_path(c, pa, 3, (120, 40, 20), 0.4)
    c.drawRect(skia.Rect(x - 170, ground - h - 30, x + 170, ground - h), fill_paint(INK))

def flaming_sword(c, x, y_top, y_bot, T, scale=1.0):
    c.drawRect(skia.Rect(x - 6 * scale, y_top, x + 6 * scale, y_bot), fill_paint((240, 230, 210)))
    c.drawRect(skia.Rect(x - 30 * scale, y_bot, x + 30 * scale, y_bot + 10 * scale), fill_paint(INK))
    n = 6
    for k in range(n):
        yy = lerp(y_top + 40 * scale, y_bot - 10, k / (n - 1))
        flame(c, x, yy + 20 * scale, 90 * scale, T + k * 0.3, seed=k, alpha=0.9, glow_=(k % 2 == 0))

def s_sword(c, lt, d, T, p):
    c.save(); camera(c, 1.0 + 0.04 * lt / d, 640, 400)
    red_world(c, T, sun=(900, 420, 160))
    gate(c, 900, GROUND)
    flaming_sword(c, 900, GROUND - 330, GROUND - 60, T)
    place(c, "masaccio_couple", 400 - 40 * lt / d, GROUND + 8, 300)
    c.restore()

def s_flames(c, lt, d, T, p):
    c.drawRect(skia.Rect(0, 0, W, H), fill_paint((30, 6, 4)))
    c.save(); camera(c, 1.0 + 0.1 * lt / d, 640, 400)
    for k, (x, h) in enumerate([(520, 420), (660, 560), (800, 460), (420, 300), (900, 340)]):
        flame(c, x, 760, h, T, seed=20 + k)
    sparks(c, 640, 500, T, 70, seed=4, spread=420)
    c.restore()

def s_couple_away(c, lt, d, T, p):
    c.save(); camera(c, lerp(1.12, 1.0, ease_out(lt / d)), 640, 420)
    red_world(c, T, sun=(1000, 450, 130), dx=30 * lt / d)
    x = 440 - 50 * lt / d
    # ombres longues vers la droite (le soleil est à droite, bas)
    c.save(); c.translate(x, GROUND + 6); c.skew(-2.2, 0); c.scale(1, -0.25)
    img = asset("masaccio_couple"); s = fit_h(img, 240)
    draw_img(c, img, 0, 0, s, anchor=(0.5, 1.0), alpha=0.35)
    c.restore()
    place(c, "masaccio_couple", x, GROUND + 6, 240)
    c.restore()

def s_fruit_falls(c, lt, d, T, p):
    vgrad(c, skia.Rect(0, 0, W, H), [(20, 4, 4), RED_SKY0])
    k = lt / d; y = lerp(60, 820, ease_in(k, 2))
    for j in range(6):
        fruit_alpha = 0.12 * (6 - j)
        c.drawCircle(640, y - j * 22, 60, fill_paint((150, 30, 20), fruit_alpha * 0.4))
    c.save(); c.translate(640, y); c.rotate(160 * k); c.translate(-640, -y); fruit(c, 640, y, 60, bite=1.0, t=T); c.restore()

# ---------- symboles (13,5-15,5 s) ----------
def gold_on_black(c):
    c.drawRect(skia.Rect(0, 0, W, H), fill_paint((12, 8, 6))); glow(c, 640, 360, 420, GOLD, 0.12)

def sym_hourglass(x=640, y=360, s=1.0):
    a, b = 150 * s, 200 * s
    return [[(x - a, y - b), (x + a, y - b)], [(x - a, y + b), (x + a, y + b)],
            [(x - a * 0.85, y - b), (x - 12, y - 8), (x - 12, y + 8), (x - a * 0.85, y + b)],
            [(x + a * 0.85, y - b), (x + 12, y - 8), (x + 12, y + 8), (x + a * 0.85, y + b)],
            [(x - a * 0.5, y + b - 5), (x, y + b - 60), (x + a * 0.5, y + b - 5)]]

def sym_tree_of_life(x=640, y=360, s=1.0):
    P = {1: (0, -250), 2: (95, -175), 3: (-95, -175), 4: (95, -60), 5: (-95, -60), 6: (0, -10), 7: (95, 60), 8: (-95, 60), 9: (0, 120), 10: (0, 230)}
    P = {k: (x + v[0] * s, y + v[1] * s) for k, v in P.items()}
    E = [(1, 2), (1, 3), (2, 3), (2, 4), (3, 5), (4, 5), (2, 6), (3, 6), (4, 6), (5, 6), (4, 7), (5, 8), (6, 7), (6, 8), (7, 8), (7, 9), (8, 9), (6, 9), (9, 10), (1, 6)]
    st = [[P[a], P[b]] for a, b in E]
    for k in range(1, 11): st.append(circle_pts(*P[k], 24 * s, 0, 360, 40))
    return st

def sym_triangle(x=640, y=380, s=1.0):
    r = 210 * s
    return [[(x, y - r), (x + r * 0.87, y + r * 0.5), (x - r * 0.87, y + r * 0.5), (x, y - r)]]

def sym_wheels(x=640, y=360, s=1.0):
    st = [circle_pts(x, y, 170 * s), circle_pts(x, y, 120 * s)]
    st.append([(x - 170 * s, y), (x + 170 * s, y)]); st.append([(x, y - 170 * s), (x, y + 170 * s)])
    return st

def s_symbol(c, lt, d, T, p):
    gold_on_black(c)
    k = p["kind"]; prog = ease_out(lt / (d * 0.45))
    c.save(); camera(c, 1.0 + 0.06 * lt / d, 640, 360)
    if k == "hourglass":
        draw_strokes(c, sym_hourglass(), prog)
        # le sable qui coule (points)
        for i in range(12): c.drawCircle(640, 368 + i * 14 + (T * 90) % 14, 2, fill_paint(GOLD, prog))
    elif k == "wheels":
        flame_a = prog
        for j, xx in enumerate((560, 720)):
            flame(c, xx, 560, 120, T, seed=40 + j, alpha=0.8 * flame_a)
        c.save(); c.translate(640, 360); c.rotate(40 * T); c.translate(-640, -360)
        draw_strokes(c, sym_wheels(), prog)
        for i in range(14):
            a = i / 14 * 2 * math.pi
            if prog > i / 14: eye_shape(c, 640 + 145 * math.cos(a), 360 + 145 * math.sin(a), 18, 6, 1.0, T)
        c.restore()
    elif k == "tree":
        draw_strokes(c, sym_tree_of_life(), prog, 2.6)
    elif k == "triangle":
        draw_strokes(c, sym_triangle(), prog, 3.4)
        if prog > 0.6: flame(c, 640, 470, 170 * ease_out((prog - 0.6) / 0.4), T, seed=50)
    c.restore()

def s_red_cut(c, lt, d, T, p):
    """Rappels d'Éden entre les symboles (sur fond rouge)."""
    k = p["kind"]
    if k == "bite":
        vgrad(c, skia.Rect(0, 0, W, H), [RED_SKY1, RED_SKY0]); c.save(); camera(c, 1.25 + 0.05 * lt / d, 700, 400); fruit(c, 640, 400, 170, bite=1.0, t=T); c.restore()
    elif k == "hand":
        reaching_hand(c, lt, d, T, red=1.0)
    elif k == "couple":
        c.save(); camera(c, 1.5, 620, 330); red_world(c, T, sun=(700, 300, 160)); place(c, "masaccio_couple", 620, GROUND + 8, 470); c.restore()
    elif k == "serpent":
        c.save(); camera(c, 1.4, 700, 460, rot=6); eden(c, T, tree_scale=1.5, base=(700, 700), sun=(520, 300, 150), red=1.0, ground=700)
        draw_serpent(c, helix(700, 690, 300, 30, 4.0), 14, t=T); c.restore()
    elif k == "sword":
        c.drawRect(skia.Rect(0, 0, W, H), fill_paint((30, 6, 4))); c.save(); camera(c, 1.6, 640, 330); flaming_sword(c, 640, 60, 620, T, 1.4); c.restore()

# ---------- la goutte d'encre tombe sur le fruit et avale l'écran (noir à 16,1 s pile) ----------
def s_ink_flood(c, lt, d, T, p):
    vgrad(c, skia.Rect(0, 0, W, H), [RED_SKY1, RED_SKY0])
    hills(c, [dict(L, col=(40, 10, 8)) for L in HOOK_HILLS[1:]])
    fruit(c, 640, 420, 90, bite=1.0, t=T)
    t_hit = d * 0.28
    if lt < t_hit:
        drop(c, 640, lerp(-40, 330, ease_in(lt / t_hit, 2)), 9, 2.2)
    else:
        k = (lt - t_hit) / (d - t_hit)
        r = 20 + 1600 * k ** 2.2
        ink_splash(c, 640, 380, r, seed=16, lobes=30, droplets=24, prog=k)

# ---------- la graine : le noir se referme en un point, racines et arbre ----------
def s_seed(c, lt, d, T, p):
    t_close = 0.45
    paper_bg(c)
    ground = 470
    if lt < t_close:
        k = ease_in(lt / t_close, 2)
        ink_splash(c, 640, ground, lerp(1500, 6, k), seed=16, lobes=30, droplets=0, halo=False)
        return
    u = (lt - t_close) / (d - t_close)
    c.save(); camera(c, lerp(1.35, 1.0, ease_io(u)), 640, lerp(ground, 400, ease_io(u)))
    # coupe du sol : terre hachurée sous la ligne
    gp = skia.Path(); gp.addRect(skia.Rect(-400, ground, W + 400, H + 400))
    c.drawPath(gp, fill_paint((205, 170, 120), clamp(u * 3)))
    hatch_path(c, gp, 3.0, INK, 0.3 * clamp(u * 3), 0.7)
    gold_line(c, [(-300, ground), (W + 300, ground)], clamp(u * 2.5), 1.8, T, head=u < 0.4, energy_=0.3)
    c.drawLine(-300, ground, -300 + (W + 600) * clamp(u * 2.5), ground, stroke_paint(INK, 1.4))
    # la graine incandescente
    glow(c, 640, ground + 6, 70 + 20 * pulse(T), FIRE, 0.8)
    c.drawOval(skia.Rect(630, ground - 2, 650, ground + 12), fill_paint((255, 200, 90)))
    g = ease_io(clamp((u - 0.12) / 0.88))
    roots(c, 640, ground + 8, 0.85, g, seed=5)
    draw_tree(c, 640, ground, 0.8, g, seed=1, leaves=True, sway=1.5, t=T)
    c.restore()
