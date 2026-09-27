"""Bibliothèque de dessin commune aux plans (style « hybride » validé, annexe A.2).
Géométries lourdes précalculées et mises en cache (arbres, foudre, réseaux)."""
import math, functools
import numpy as np, skia, cv2
from engine.core import *

# ---------- bruit ----------
def noise1d(n, seed=0, octaves=4, base=8):
    """Bruit fractal 1D (n échantillons, ~[-1, 1])."""
    rng = np.random.default_rng(seed); out = np.zeros(n)
    for o in range(octaves):
        k = base * 2 ** o
        v = rng.uniform(-1, 1, k + 3)
        x = np.linspace(0, k, n)
        out += np.interp(x, np.arange(k + 3), v) / 2 ** o
    return out / 1.9

# ---------- caméra ----------
def camera(c, zoom=1.0, cx=W / 2, cy=H / 2, dx=0.0, dy=0.0, rot=0.0):
    """Zoom autour de (cx, cy) + décalage + rotation (degrés)."""
    c.translate(W / 2 + dx, H / 2 + dy); c.rotate(rot); c.scale(zoom, zoom); c.translate(-cx, -cy)

def punch(lt, amp=0.05, dur=0.18):
    """« Zoom punch » bref en début de plan (impacts sur temps forts)."""
    return 1 + amp * (1 - ease_out(lt / dur, 2)) if lt < dur else 1.0

def shake(t, amp=3.0, seed=0):
    rng = np.random.default_rng(seed + frame_of(t)); return rng.uniform(-amp, amp, 2)

# ---------- fonds ----------
def paper_bg(c, tint=PAPER, seed=3):
    c.drawImage(paper_tex(W, H, tint, seed), 0, 0)

def sky(c, top, bottom, y0=0, y1=H, lines=True, alpha=0.43, horizon=None):
    """Ciel en dégradé + gravure : lignes horizontales fines, plus serrées vers l'horizon."""
    vgrad(c, skia.Rect(0, y0, W, y1), [top, bottom])
    if lines:
        hz = horizon if horizon is not None else y1
        p = stroke_paint(INK, 0.7, alpha * 0.55)
        y = y0 + 2.0; step = 7.0
        while y < hz:
            c.drawLine(0, y, W, y, p)
            d = (hz - y) / max(1, hz - y0)                 # 1 en haut, 0 à l'horizon
            step = 2.6 + 6.5 * d; y += step

def engraved_sun(c, x, y, r, fill=(250, 232, 180), ring=INK, rings=7, alpha=1.0, line_col=None, t=0.0, breathe=0.0):
    """Soleil plein + anneaux concentriques gravés autour + fines lignes horizontales dedans."""
    rr = r * (1 + breathe)
    for k in range(rings, 0, -1):
        c.drawCircle(x, y, rr + k * r * 0.085, stroke_paint(ring, 0.8, 0.35 * alpha * (1 - k / (rings + 1))))
    c.drawCircle(x, y, rr, fill_paint(fill, alpha))
    c.save(); pth = skia.Path(); pth.addCircle(x, y, rr); c.clipPath(pth, doAntiAlias=True)
    lp = stroke_paint(line_col or mix(fill, INK, 0.25), 0.8, 0.5 * alpha)
    yy = y - rr
    while yy < y + rr:
        c.drawLine(x - rr, yy, x + rr, yy, lp); yy += 3.2 + 2.0 * (1 - (yy - (y - rr)) / (2 * rr))
    c.restore()
    c.drawCircle(x, y, rr, stroke_paint(ring, 1.3, 0.8 * alpha))

def hill_path(y_base, amp, seed, x0=-50, x1=W + 50, n=160, base=4, bottom=H + 50):
    xs = np.linspace(x0, x1, n); ys = y_base + amp * noise1d(n, seed, 4, base)
    p = skia.Path(); p.moveTo(x0, bottom)
    for x, y in zip(xs, ys): p.lineTo(float(x), float(y))
    p.lineTo(x1, bottom); p.close()
    return p, list(zip(xs.tolist(), ys.tolist()))

def hatch_path(c, path, step=3.0, col_=INK, a=0.35, width=0.7, cross=False, angle=0.0):
    """Hachures horizontales (croisées si demandé) dans un chemin."""
    b = path.getBounds(); c.save(); c.clipPath(path, doAntiAlias=True)
    p = stroke_paint(col_, width, a)
    y = b.top()
    while y < b.bottom():
        c.drawLine(b.left(), y, b.right(), y + angle, p); y += step
    if cross:
        x = b.left() - b.height()
        while x < b.right():
            c.drawLine(x, b.bottom(), x + b.height() * 0.7, b.top(), p); x += step * 1.6
    c.restore()

def hills(c, layers, dx=0.0):
    """layers : liste de dict(y, amp, seed, col, par, step, a, cross). Parallaxe via par*dx."""
    tops = []
    for L in layers:
        c.save(); c.translate(dx * L.get("par", 1.0), 0)
        p, top = hill_path(L["y"], L["amp"], L["seed"], x0=-300, x1=W + 300, base=L.get("base", 4))
        c.drawPath(p, fill_paint(L["col"]))
        hatch_path(c, p, L.get("step", 3.0), INK, L.get("a", 0.3), 0.7, L.get("cross", False))
        c.drawPath(path_from(top), stroke_paint(INK, 1.0, 0.6))
        c.restore(); tops.append(top)
    return tops

def grass(c, y, x0=0, x1=W, seed=0, h=10, dens=0.7, col_=INK, a=0.9, sway=0.0):
    """Herbe en traits de plume fins."""
    rng = np.random.default_rng(seed); x = x0
    p = stroke_paint(col_, 0.9, a)
    while x < x1:
        hh = h * rng.uniform(0.4, 1.3); lean = rng.uniform(-0.5, 0.5) * hh + sway * hh
        pa = skia.Path(); pa.moveTo(x, y); pa.quadTo(x + lean * 0.3, y - hh * 0.6, x + lean, y - hh); c.drawPath(pa, p)
        x += rng.uniform(1.5, 5.0) / dens

# ---------- papier vierge + monde coloré (le hook) ----------
def torn_edge(x_front, seed=0, amp=10.0, n=90):
    ys = np.linspace(-20, H + 20, n); xs = x_front + amp * noise1d(n, seed, 4, 6)
    return list(zip(xs.tolist(), ys.tolist()))

def world_clip(c, x_front, seed=0, left=True):
    """Clip sur la partie gauche (monde coloré) d'une frontière déchirée verticale."""
    edge = torn_edge(x_front, seed)
    p = skia.Path(); p.moveTo(-10 if left else W + 10, -20)
    for x, y in edge: p.lineTo(x, y)
    p.lineTo(-10 if left else W + 10, H + 20); p.close()
    c.clipPath(p, doAntiAlias=True)
    return edge

def pencil_lines(c, tops, a=0.35):
    """Esquisse au crayon du monde à venir (sur le papier vierge)."""
    p = stroke_paint((95, 90, 85), 0.8, a)
    for top in tops: c.drawPath(path_from(top), p)

# ---------- encre ----------
def ink_splash(c, x, y, r, seed=0, col_=INK, lobes=30, droplets=18, halo=True, prog=1.0):
    """Tache d'encre (annexe A.4) : lobes arrondis (gaussiennes angulaires larges), bord bruité, gouttelettes, halo."""
    rng = np.random.default_rng(seed)
    n = 240; ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rad = np.ones(n)
    for _ in range(lobes):
        a0 = rng.uniform(0, 2 * np.pi); w = rng.uniform(0.12, 0.35); h = rng.uniform(0.05, 0.35)
        d = np.angle(np.exp(1j * (ang - a0))); rad += h * np.exp(-(d / w) ** 2)
    rad += 0.04 * noise1d(n, seed + 1, 4, 12)
    rad = rad / rad.max() * r
    if halo:
        pts = [(x + 1.06 * rr * math.cos(a), y + 1.06 * rr * math.sin(a)) for a, rr in zip(ang, rad)]
        c.drawPath(path_from(pts, True), fill_paint(col_, 0.18))
    pts = [(x + rr * math.cos(a), y + rr * math.sin(a)) for a, rr in zip(ang, rad)]
    c.drawPath(path_from(pts, True), fill_paint(col_))
    for k in range(droplets):
        a = rng.uniform(0, 2 * np.pi); d = r * rng.uniform(1.05, 1.9) * (0.5 + 0.5 * prog); s = r * rng.uniform(0.015, 0.07)
        c.drawCircle(x + d * math.cos(a), y + d * math.sin(a), s, fill_paint(col_))

def drop(c, x, y, r, stretch=1.6, col_=INK):
    """Goutte qui tombe (allongée)."""
    p = skia.Path(); p.addOval(skia.Rect(x - r, y - r * stretch, x + r, y + r)); c.drawPath(p, fill_paint(col_))

# ---------- arbre récursif (L-system à largeur décroissante) ----------
@functools.lru_cache(maxsize=16)
def tree_geom(seed=1, depth=8, trunk=120.0, spread=24.0, shrink=0.76, width=9.0):
    """Liste de branches (x0, y0, x1, y1, w0, w1, gen, t0) dans un repère où la base est (0, 0), vers le haut ;
    t0 = instant normalisé de naissance (pour la croissance). Feuilles (x, y, angle, gen)."""
    rng = np.random.default_rng(seed); br = []; leaves = []
    def rec(x, y, ang, L, w, g, t0):
        x1 = x + L * math.sin(math.radians(ang)); y1 = y - L * math.cos(math.radians(ang))
        br.append((x, y, x1, y1, w, w * shrink, g, t0))
        if g >= depth:
            for _ in range(3):
                leaves.append((x1 + rng.normal(0, 4), y1 + rng.normal(0, 4), rng.uniform(0, 360), g)); return
            return
        k = 2 if rng.uniform() < 0.8 else 3
        for i in range(k):
            a = ang + (i - (k - 1) / 2) * spread * rng.uniform(0.7, 1.3) + rng.normal(0, 5)
            a += (0 - ang) * 0.12                    # port en parasol (acacia) : les branches remontent
            rec(x1, y1, a, L * shrink * rng.uniform(0.85, 1.12), w * shrink, g + 1, t0 + 1.0 / (depth + 1))
        if g >= depth - 3:
            for _ in range(2): leaves.append((x1 + rng.normal(0, 6), y1 + rng.normal(0, 6), rng.uniform(0, 360), g))
    rec(0, 0, 0, trunk, width, 0, 0.0)
    return br, leaves

def draw_tree(c, x, y, scale=1.0, grow=1.0, seed=1, col_=INK, leaf_col=None, leaves=True, sway=0.0, t=0.0, depth=8):
    """Arbre qui s'effile ; croissance génération par génération (grow 0..1) ; feuillage en petites feuilles effilées."""
    br, lv = tree_geom(seed, depth)
    c.save(); c.translate(x, y); c.scale(scale, scale)
    p = skia.Paint(AntiAlias=True, Color4f=col(col_), Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap)
    for (x0, y0, x1, y1, w0, w1, g, t0) in br:
        f = clamp((grow - t0) * (depth + 1))
        if f <= 0: continue
        sw = sway * (g / depth) ** 2 * math.sin(t * 1.3 + g)
        xe, ye = x0 + (x1 - x0) * f + sw, y0 + (y1 - y0) * f
        p.setStrokeWidth((w0 + w1) / 2); c.drawLine(x0, y0, xe, ye, p)
    if leaves:
        lp = fill_paint(leaf_col or col_)
        for (lx, ly, a, g) in lv:
            f = clamp((grow - 0.85) / 0.15)
            if f <= 0: break
            c.save(); c.translate(lx, ly); c.rotate(a); s = 3.2 * f
            pa = skia.Path(); pa.moveTo(-s * 1.8, 0); pa.quadTo(0, -s * 0.9, s * 1.8, 0); pa.quadTo(0, s * 0.9, -s * 1.8, 0)
            c.drawPath(pa, lp); c.restore()
    c.restore()

def roots(c, x, y, scale=1.0, grow=1.0, seed=5, col_=INK):
    """Racines = le même arbre, inversé (symétrie arbre / racines)."""
    c.save(); c.translate(x, y); c.scale(1, -1); draw_tree(c, 0, 0, scale * 0.8, grow, seed, col_, leaves=False, depth=7); c.restore()

# ---------- fruit ----------
def fruit(c, x, y, r, bite=0.0, t=0.0, shine=True, stem=True):
    """Fruit rouge (seul saturé) ; bite 0..1 = morsure qui apparaît."""
    body = skia.Path(); body.addCircle(x, y, r)
    if bite > 0:
        b = skia.Path(); br = r * 0.42 * ease_out(bite)
        for k in range(3):
            b.addCircle(x + r * 0.92, y - r * 0.15 + (k - 1) * br * 0.75, br)
        body = skia.Op(body, b, skia.PathOp.kDifference_PathOp)
    sh = skia.GradientShader.MakeRadial(skia.Point(x - r * 0.35, y - r * 0.4), r * 1.5, [col((250, 120, 70)), col((200, 40, 25)), col((90, 12, 10))], [0, 0.55, 1])
    c.drawPath(body, skia.Paint(AntiAlias=True, Shader=sh))
    c.save(); c.clipPath(body, doAntiAlias=True)
    lp = stroke_paint(INK, 0.8, 0.25); yy = y - r
    while yy < y + r: c.drawLine(x - r, yy, x + r, yy, lp); yy += 3.0
    c.restore()
    c.drawPath(body, stroke_paint(INK, 2.2))
    if bite > 0:
        c.save(); c.clipPath(body, doAntiAlias=True)
        c.drawCircle(x + r * 0.92, y - r * 0.15, r * 0.42 * ease_out(bite) + 3, stroke_paint((250, 235, 200), 5, 0.9)); c.restore()
    if shine:
        pa = skia.Path(); pa.addArc(skia.Rect(x - r * 0.7, y - r * 0.75, x + r * 0.2, y + r * 0.1), 200, 60)
        c.drawPath(pa, stroke_paint((255, 230, 210), r * 0.06, 0.8))
    if stem:
        pa = skia.Path(); pa.moveTo(x, y - r * 0.9); pa.quadTo(x + r * 0.1, y - r * 1.3, x + r * 0.05, y - r * 1.6)
        c.drawPath(pa, stroke_paint(INK, r * 0.07))
        lf = skia.Path(); lx, ly = x + r * 0.05, y - r * 1.45
        lf.moveTo(lx, ly); lf.quadTo(lx + r * 0.5, ly - r * 0.45, lx + r * 1.0, ly - r * 0.15); lf.quadTo(lx + r * 0.5, ly + r * 0.1, lx, ly)
        c.drawPath(lf, fill_paint(INK))

# ---------- flammes (vivantes : respiration, langues) ----------
def flame(c, x, y, h, t, seed=0, w=None, alpha=1.0, glow_=True):
    """Flamme en langues superposées (or -> orange -> rouge), qui respire et vacille."""
    w = w or h * 0.42; rng = np.random.default_rng(seed)
    if glow_: glow(c, x, y - h * 0.4, h * 1.4, FIRE, 0.45 * alpha)
    for layer, (cc, s) in enumerate([((200, 50, 20), 1.0), ((250, 120, 30), 0.78), ((255, 200, 80), 0.55), ((255, 245, 200), 0.3)]):
        n = 5
        for k in range(n):
            ph = rng.uniform(0, 6.28); sp = rng.uniform(5, 9)
            hh = h * s * (0.65 + 0.35 * math.sin(t * sp + ph)) * rng.uniform(0.7, 1.0)
            ww = w * s * rng.uniform(0.4, 0.8)
            ox = (k - (n - 1) / 2) * w * s * 0.28 + math.sin(t * 7 + ph) * w * 0.08
            tipx = x + ox + math.sin(t * 5 + ph) * w * 0.35
            pa = skia.Path(); pa.moveTo(x + ox - ww / 2, y)
            pa.cubicTo(x + ox - ww * 0.6, y - hh * 0.5, tipx - ww * 0.1, y - hh * 0.8, tipx, y - hh)
            pa.cubicTo(tipx + ww * 0.1, y - hh * 0.8, x + ox + ww * 0.6, y - hh * 0.5, x + ox + ww / 2, y)
            pa.close(); c.drawPath(pa, fill_paint(cc, alpha * 0.92))

def sparks(c, x, y, t, n=40, seed=0, spread=160, life=1.0, col_=(255, 210, 120), up=True):
    rng = np.random.default_rng(seed)
    for i in range(n):
        ph = rng.uniform(0, life); a = rng.uniform(-math.pi, 0) if up else rng.uniform(0, 2 * math.pi)
        v = rng.uniform(0.3, 1.0) * spread; tt = ((t + ph) % life) / life
        px = x + math.cos(a) * v * tt; py = y + math.sin(a) * v * tt + 60 * tt * tt
        c.drawCircle(px, py, 1.6 * (1 - tt) + 0.4, fill_paint(col_, 1 - tt))

# ---------- foudre (Lichtenberg) ----------
@functools.lru_cache(maxsize=16)
def lightning_geom(seed=0, length=520.0, segs=26):
    rng = np.random.default_rng(seed); out = []
    def bolt(x, y, ang, L, w, depth):
        pts = [(x, y)]; n = max(4, int(segs * L / length))
        for i in range(n):
            ang2 = ang + rng.normal(0, 0.45); x += math.sin(ang2) * L / n; y += math.cos(ang2) * L / n
            pts.append((x, y))
            if depth < 3 and rng.uniform() < 0.18:
                bolt(x, y, ang + rng.choice([-1, 1]) * rng.uniform(0.4, 0.9), L * rng.uniform(0.25, 0.5), w * 0.55, depth + 1)
        out.append((pts, w))
    bolt(0, 0, 0, length, 3.0, 0)
    return out

def draw_lightning(c, x, y, prog, seed=0, scale=1.0, a=1.0):
    for pts, w in lightning_geom(seed):
        n = max(2, int(len(pts) * clamp(prog)))
        pp = [(x + px * scale, y + py * scale) for px, py in pts[:n]]
        gp = stroke_paint((190, 200, 255), w * 5, 0.25 * a); gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
        c.drawPath(path_from(pp), gp); c.drawPath(path_from(pp), stroke_paint((245, 245, 255), w, a))

# ---------- étoiles ----------
@functools.lru_cache(maxsize=8)
def star_field(seed=0, n=260):
    rng = np.random.default_rng(seed)
    return rng.uniform(0, W, n), rng.uniform(0, H, n), rng.uniform(0.4, 1.6, n), rng.uniform(0, 6.28, n)

def stars(c, t, seed=0, a=1.0, dx=0.0, n=260):
    xs, ys, ss, ph = star_field(seed, n)
    for x, y, s, p in zip(xs, ys, ss, ph):
        c.drawCircle(float((x + dx) % W), float(y), float(s), fill_paint((240, 230, 200), a * (0.5 + 0.5 * math.sin(t * 2 + p))))

# ---------- symboles (traits d'or qui se dessinent en éclair) ----------
def draw_strokes(c, strokes, prog, width=3.0, col_=GOLD, glow_a=0.35):
    """strokes : liste de polylignes ; se dessinent l'une après l'autre sur prog 0..1."""
    tot = sum(max(1e-3, np.sum(np.sqrt(np.sum(np.diff(np.asarray(s), axis=0) ** 2, 1)))) for s in strokes)
    acc = 0.0
    for s in strokes:
        s = np.asarray(s, np.float32); L = float(np.sum(np.sqrt(np.sum(np.diff(s, axis=0) ** 2, 1))))
        f = clamp((prog * tot - acc) / max(1e-3, L)); acc += L
        if f <= 0: break
        part, _, _ = polyline_partial(s, f)
        pa = path_from(part.tolist())
        gp = stroke_paint(col_, width * 4, glow_a); gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)); c.drawPath(pa, gp)
        c.drawPath(pa, stroke_paint(col_, width))

def circle_pts(x, y, r, a0=0, a1=360, n=90):
    return [(x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]

# ---------- meandre (frise grecque) ----------
def meander_band(c, y, h, col_=INK, bg=None, x_off=0.0, unit=None):
    """Frise de méandres (clé grecque) sur une bande horizontale."""
    if bg: c.drawRect(skia.Rect(0, y, W, y + h), fill_paint(bg))
    u = unit or h / 5.0; p = stroke_paint(col_, u * 0.7, 1.0, skia.Paint.kSquare_Cap)
    x = -((x_off) % (u * 5)) - u * 5
    while x < W + u * 5:
        pts = [(x, y + h - u), (x + 4 * u, y + h - u), (x + 4 * u, y + u), (x + u, y + u), (x + u, y + 3 * u), (x + 3 * u, y + 3 * u), (x + 3 * u, y + 2 * u)]
        c.drawPath(path_from(pts), p); x += 5 * u
    c.drawLine(0, y + u * 0.2, W, y + u * 0.2, stroke_paint(col_, 1.5)); c.drawLine(0, y + h - u * 0.2, W, y + h - u * 0.2, stroke_paint(col_, 1.5))

# ---------- divers ----------
def dust(c, t, seed=0, n=60, col_=(250, 235, 200), a=0.6, drift=(8, -4), box=(0, 0, W, H), size=1.2):
    """Micro-vie : poussière / pollen qui dérive lentement."""
    rng = np.random.default_rng(seed); x0, y0, x1, y1 = box
    for i in range(n):
        x = x0 + (rng.uniform(0, 1) * (x1 - x0) + drift[0] * t * rng.uniform(0.5, 1.5)) % (x1 - x0)
        y = y0 + (rng.uniform(0, 1) * (y1 - y0) + drift[1] * t * rng.uniform(0.5, 1.5)) % (y1 - y0)
        c.drawCircle(x, y, size * rng.uniform(0.5, 1.4), fill_paint(col_, a * (0.4 + 0.6 * abs(math.sin(t * 1.7 + i)))))

def flash(c, amount, col_=(255, 240, 210)):
    if amount > 0: c.drawRect(skia.Rect(0, 0, W, H), fill_paint(col_, clamp(amount)))

def vignette(c, a=0.5, col_=INK):
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * 0.75, [col(col_, 0), col(col_, 0), col(col_, a)], [0, 0.55, 1])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))

def shadowed(c, img, x, y, scale=1.0, off=(6, 8), blur=6, a=0.45, flip=False, anchor=(0.5, 0.5), rot=0.0):
    """Pièce de papier découpée avec ombre portée (visages, silhouettes)."""
    c.save()
    if flip: c.translate(x, y); c.scale(-1, 1); c.translate(-x, -y)
    p = skia.Paint(AntiAlias=True); p.setImageFilter(skia.ImageFilters.DropShadowOnly(off[0] * (-1 if flip else 1), off[1], blur, blur, col(INK, a)))
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(scale, scale)
    r = skia.Rect.MakeXYWH(-img.width() * anchor[0], -img.height() * anchor[1], img.width(), img.height())
    c.drawImageRect(img, r, SAMPLING, p); c.drawImageRect(img, r, SAMPLING, skia.Paint(AntiAlias=True))
    c.restore(); c.restore()
