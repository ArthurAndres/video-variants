"""Plans 0:40,8-0:50 : le feu se propage. Une coupe par temps (chaque image une seule fois), puis le réseau de feu
recule sans fin jusqu'à l'embrasement doré. Impacts sur les temps : punch, flash, étincelles (intensité 6 bis)."""
import math, functools
import numpy as np, skia
from scipy.spatial import Delaunay
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import minimum_spanning_tree, shortest_path
from engine.core import *
from engine.common import *
from engine.shots_a import fit_h, place
from engine.shots_b import dark_bg

# ---------- réseau de feu : arbre couvrant minimal depuis le centre, allumage calé sur la distance ----------
@functools.lru_cache(maxsize=4)
def fire_net(n=2600, R=4200.0, seed=7):
    rng = np.random.default_rng(seed)
    r = R * np.sqrt(rng.uniform(0, 1, n)) ** 1.35; a = rng.uniform(0, 2 * np.pi, n)
    P = np.c_[r * np.cos(a), r * np.sin(a) * 0.62]; P[0] = 0
    tri = Delaunay(P); E = set()
    for s in tri.simplices:
        for i in range(3):
            u, v = sorted((s[i], s[(i + 1) % 3])); E.add((u, v))
    E = np.array(list(E)); w = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
    G = coo_matrix((w, (E[:, 0], E[:, 1])), shape=(n, n))
    T = minimum_spanning_tree(G).tocoo()
    edges = np.c_[T.row, T.col]
    dist = shortest_path(T, directed=False, indices=0)
    return P, edges, dist

def draw_net(c, t_light, cx, cy, scale, rot=0.0, wave_t=None, a=1.0, speed=900.0, heat=0.5):
    """t_light : temps écoulé depuis l'allumage du centre ; un nœud s'allume quand dist/speed < t_light.
    Arêtes regroupées en un seul chemin (rapide) : halo flou (bloom) + trait net."""
    P, E, D = fire_net()
    ca, sa = math.cos(rot), math.sin(rot)
    X = cx + scale * (P[:, 0] * ca - P[:, 1] * sa); Y = cy + scale * (P[:, 0] * sa + P[:, 1] * ca)
    lit = D / speed < t_light
    vis = (X > -80) & (X < W + 80) & (Y > -80) & (Y < H + 80)
    on = skia.Path(); off = skia.Path()
    for u, v in E:
        if not (vis[u] or vis[v]): continue
        pth = on if (lit[u] and lit[v]) else off
        pth.moveTo(X[u], Y[u]); pth.lineTo(X[v], Y[v])
    w = clamp(1.2 + 0.9 * scale, 1.2, 3.2)
    c.drawPath(off, stroke_paint((90, 84, 110), 1.0, 0.5 * a))
    gp = stroke_paint(FIRE, w * 6, (0.25 + 0.3 * heat) * a); gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)); gp.setBlendMode(skia.BlendMode.kPlus)
    c.drawPath(on, gp)
    c.drawPath(on, stroke_paint((255, 206, 110), w, a))
    fresh = lit & (D / speed > t_light - 0.3) & vis
    nodes = skia.Path()
    for i in np.where(lit & vis)[0]: nodes.addCircle(float(X[i]), float(Y[i]), w * 1.1)
    c.drawPath(nodes, fill_paint((255, 240, 200), a))
    for i in np.where(fresh)[0][:60]:
        flame(c, X[i], Y[i], 22 * clamp(scale, 0.4, 1.5), t_light + i, seed=int(i % 7), glow_=True, alpha=0.9 * a)
    if wave_t is not None:
        # onde dorée sur chaque temps : anneau lumineux qui traverse le réseau
        rr = 60 + wave_t * 1500; al = clamp(1 - wave_t / 0.42)
        wp = stroke_paint((255, 180, 70), 8, 0.5 * al * a); wp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)); wp.setBlendMode(skia.BlendMode.kPlus)
        c.drawCircle(cx, cy, rr, wp)

def impact(c, lt, amount=0.35):
    flash(c, amount * clamp(1 - lt / 0.08), (255, 230, 180))

def s_net_macro(c, lt, d, T, p):
    dark_bg(c, (12, 12, 20))
    c.save(); camera(c, punch(lt, 0.06))
    draw_net(c, 0.6 + lt * 1.5, 640, 360, 1.9, rot=0.05, heat=0.4)
    c.restore(); impact(c, lt, 0.45)

def s_bearers(c, lt, d, T, p):
    vgrad(c, skia.Rect(0, 0, W, H), [(20, 16, 24), (60, 30, 20)])
    c.save(); camera(c, punch(lt, 0.05), 640, 400, dx=-60 * lt / d)
    xs = np.linspace(120, 1180, 6)                 # espacés : jamais de chevauchement
    for i, x in enumerate(xs):
        s = 0.62 + 0.3 * i / 5
        y = 610 - 8 * i
        place(c, "runner_torch_sil", float(x), y, 250 * s, a=0.25)
        img = asset("runner_torch_sil"); tx, ty, iw, ih = alpha_extent_rt()
        sc = 250 * s / img.height()
        fx = x + (tx - iw / 2) * sc; fy = y - ih * sc + ty * sc
        if lt > i * 0.04: flame(c, float(fx), float(fy), 40 * s, T + i, seed=i)
    c.drawRect(skia.Rect(-10, 612, W + 10, H + 10), fill_paint((20, 12, 10)))
    c.restore(); impact(c, lt, 0.25)

@functools.lru_cache(maxsize=1)
def alpha_extent_rt():
    from engine.shots_a import alpha_extent
    return alpha_extent("runner_torch_sil", 0, 0.45, "right")

def s_net_medium(c, lt, d, T, p):
    dark_bg(c, (12, 12, 20))
    c.save(); camera(c, punch(lt, 0.05))
    draw_net(c, 1.4 + lt * 1.5, 640, 360, 0.9, rot=-0.08)
    c.restore(); impact(c, lt, 0.25)

def s_shadow_gold(c, lt, d, T, p):
    """L'ombre de Prométhée (le coureur du vase) découpée sur une lumière dorée, sans liseré."""
    c.drawRect(skia.Rect(0, 0, W, H), fill_paint((40, 22, 10)))
    glow(c, 760, 330, 520, (255, 210, 120), 1.0)
    glow(c, 760, 330, 260, (255, 240, 200), 0.8)
    c.save(); camera(c, punch(lt, 0.05) * (1 + 0.04 * lt / d), 640, 360)
    img = asset("runner_torch_sil"); s = fit_h(img, 820)
    draw_img(c, img, 600, 400, s)
    c.restore()

def anvil(c, x, y, s=1.0, heat=0.0):
    pa = skia.Path(); pa.moveTo(x - 190 * s, y - 60 * s); pa.lineTo(x + 170 * s, y - 60 * s); pa.quadTo(x + 260 * s, y - 55 * s, x + 300 * s, y - 80 * s)
    pa.lineTo(x + 250 * s, y - 20 * s); pa.lineTo(x + 90 * s, y - 10 * s); pa.lineTo(x + 70 * s, y + 90 * s); pa.lineTo(x + 140 * s, y + 140 * s)
    pa.lineTo(x - 150 * s, y + 140 * s); pa.lineTo(x - 80 * s, y + 90 * s); pa.lineTo(x - 100 * s, y - 10 * s); pa.lineTo(x - 190 * s, y - 20 * s); pa.close()
    c.drawPath(pa, fill_paint(INK)); hatch_path(c, pa, 3, (120, 70, 40), 0.35)
    c.drawRect(skia.Rect(x - 60 * s, y - 72 * s, x + 80 * s, y - 60 * s), fill_paint(mix((200, 70, 20), (255, 230, 150), heat)))
    glow(c, x + 10 * s, y - 66 * s, 120 * s, FIRE, 0.5 + 0.4 * heat)

def hammer(c, x, y, ang, s=1.0):
    c.save(); c.translate(x, y); c.rotate(ang)
    c.drawRect(skia.Rect(-8 * s, -300 * s, 8 * s, 0), fill_paint((70, 44, 28)))
    c.drawRect(skia.Rect(-50 * s, -340 * s, 50 * s, -290 * s), fill_paint(INK))
    c.restore()

def s_forge_up(c, lt, d, T, p):
    dark_bg(c, (16, 10, 8))
    c.save(); camera(c, punch(lt, 0.05) * 1.45, 700, 470)
    anvil(c, 620, 560, 1.0, 0.3)
    hammer(c, 900, 700, -35 - 8 * ease_out(lt / d))
    sparks(c, 640, 490, T, 20, seed=2, spread=120)
    c.restore()

def s_forge_down(c, lt, d, T, p):
    dark_bg(c, (16, 10, 8))
    c.save(); camera(c, punch(lt, 0.1) * 1.3, 640, 470); o = shake(T, 5 * clamp(1 - lt / 0.15))
    c.translate(o[0], o[1])
    anvil(c, 620, 560, 1.0, 1.0 - 0.6 * lt / d)
    hammer(c, 900, 700, 2)
    # gerbe d'étincelles sur le temps
    rng = np.random.default_rng(9)
    for i in range(160):
        a = rng.uniform(-math.pi, 0); v = rng.uniform(200, 900); tt = lt
        x = 640 + math.cos(a) * v * tt; y = 494 + math.sin(a) * v * tt + 900 * tt * tt
        c.drawLine(x, y, x - math.cos(a) * 14, y - math.sin(a) * 14 - 900 * tt * 0.03, stroke_paint((255, 210, 120), 2, clamp(1 - tt / 0.45)))
    c.restore(); impact(c, lt, 0.5)

def s_bellows(c, lt, d, T, p):
    """Le four respire : gueule de briques, le feu enfle sur chaque temps (le poumon de la forge)."""
    dark_bg(c, (16, 10, 8))
    br = pulse(T, 0.2)
    c.save(); camera(c, punch(lt, 0.05) * (1 + 0.05 * lt / d), 640, 400)
    arch = skia.Path(); arch.addRect(skia.Rect(300, 360, 980, 720)); arch.addCircle(640, 360, 340)
    arch.setFillType(skia.PathFillType.kWinding)
    mouth = skia.Path(); mouth.addRect(skia.Rect(470, 420, 810, 640)); mouth.addCircle(640, 420, 170)
    c.drawPath(arch, fill_paint((90, 44, 28)))
    c.save(); c.clipPath(arch, doAntiAlias=True)
    for j in range(0, 400, 28):
        y = 20 + j; c.drawLine(0, y, W, y, stroke_paint(INK, 2, 0.8))
        off = 30 if (j // 28) % 2 else 0
        for x in range(260 + off, 1000, 60): c.drawLine(x, y, x, y + 28, stroke_paint(INK, 2, 0.8))
    c.restore()
    c.drawPath(mouth, fill_paint((40, 10, 4)))
    c.save(); c.clipPath(mouth, doAntiAlias=True)
    glow(c, 640, 560, 260 + 120 * br, FIRE, 0.7 + 0.3 * br)
    for k, x in enumerate((540, 600, 660, 720)): flame(c, x, 650, 150 + 110 * br, T, seed=30 + k, glow_=False)
    c.restore()
    sparks(c, 640, 420, T, 30, seed=13, spread=220)
    c.restore()

def s_pour(c, lt, d, T, p):
    dark_bg(c, (14, 10, 10))
    c.save(); camera(c, punch(lt, 0.05) * (1 + 0.06 * lt / d), 640, 360)
    ang = -18 - 22 * ease_out(lt / d)
    c.save(); c.translate(470, 260); c.rotate(ang)
    cr = skia.Path(); cr.moveTo(-90, -70); cr.lineTo(90, -70); cr.lineTo(70, 70); cr.lineTo(-70, 70); cr.close()
    c.drawPath(cr, fill_paint((60, 40, 30))); hatch_path(c, cr, 3, INK, 0.5)
    c.drawRect(skia.Rect(-80, -74, 80, -60), fill_paint((255, 180, 60)))
    c.restore()
    st = skia.Path(); st.moveTo(560, 250); st.cubicTo(600, 300, 620, 420, 630, 640); st.lineTo(650, 640); st.cubicTo(640, 420, 620, 300, 575, 245); st.close()
    c.drawPath(st, fill_paint((255, 200, 90)))
    glow(c, 640, 560, 260, FIRE, 0.6)
    mold = skia.Rect(470, 600, 810, 700); c.drawRect(mold, fill_paint(INK))
    c.drawRect(skia.Rect(500, 610, 780, 630), fill_paint((255, 170, 60), 0.4 + 0.6 * lt / d))
    sparks(c, 640, 600, T, 50, seed=12, spread=260)
    c.restore()

def s_net_recede(c, lt, d, T, p):
    """Un seul plan continu : le réseau recule sans fin (×1,6 -> ×0,2), onde dorée sur chaque temps, jusqu'à l'embrasement."""
    u = lt / d
    dark_bg(c, (12, 12, 20))
    scale = math.exp(lerp(math.log(1.6), math.log(0.2), ease_in(u, 1.3)))
    b, _ = last_beat(T); wave = T - b
    draw_net(c, 3.0 + lt * 2.2, 640, 360, scale, rot=0.25 * u, wave_t=wave, heat=0.4 + 0.6 * u)
    flash(c, 0.12 * pulse(T, 0.1) * u, (255, 220, 160))
    # l'embrasement doré : l'or envahit tout, avec la texture du papier gravé
    g = ease_in(clamp((u - 0.72) / 0.28), 2)
    if g > 0:
        c.drawRect(skia.Rect(0, 0, W, H), fill_paint((246, 190, 90), g))
        glow(c, 640, 360, 700, (255, 245, 210), g)
        c.drawImage(paper_tex(W, H, (250, 200, 110), 5), 0, 0, SAMPLING, skia.Paint(Alphaf=0.5 * g, BlendMode=skia.BlendMode.kMultiply))
