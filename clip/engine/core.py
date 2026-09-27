"""Moteur commun : horloge musicale, palette, papier, outils Skia, ligne d'or, finition.
Tout est déterministe (graines fixes). Mise en page en 1280×720 (mode final 20 bis) ; preview = même dessin réduit."""
import json, math, functools, os
import numpy as np, cv2, skia

W, H, FPS = 1280, 720, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- horloge musicale ----------
_A = json.load(open(os.path.join(ROOT, "analysis/analysis.json")))
ATTACK = 0.017                                   # le son commence 17 ms avant le pic d'attaque (étude du test)
BEATS = np.array(_A["temps_s"]) - ATTACK
_E = np.array(_A["energie"]["valeurs"]); _EST = _A["energie"]["pas_s"]

def beat(i):
    """Instant du temps i (demi-temps si i non entier)."""
    i0 = int(math.floor(i)); f = i - i0
    if f == 0: return float(BEATS[i0])
    return float(BEATS[i0] + f * (BEATS[i0 + 1] - BEATS[i0]))

def frame_of(t): return int(round(t * FPS))
def energy(t): return float(np.interp(t, np.arange(len(_E)) * _EST + _EST / 2, _E))

def last_beat(t, sub=1):
    """Dernier temps (ou subdivision) avant t, et son index."""
    grid = BEATS if sub == 1 else np.sort(np.concatenate([BEATS] + [BEATS[:-1] + k / sub * np.diff(BEATS) for k in range(1, sub)]))
    j = np.searchsorted(grid, t, side="right") - 1
    return (float(grid[j]) if j >= 0 else -1e9), j

def pulse(t, decay=0.16, sub=1):
    """Respiration sur les temps : 1 au temps, décroît en exp(-dt/0,16)."""
    b, _ = last_beat(t, sub)
    return math.exp(-(t - b) / decay) if t >= b else 0.0

# ---------- palette (annexe A.2) ----------
def rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
INK = rgb("#16100D"); PAPER = rgb("#F0E4C8"); OCHRE_HI = rgb("#EECC8A"); OCHRE_LO = rgb("#D89448")
TERRA = rgb("#C66C3C"); CLAY = rgb("#BE6030"); GOLD = rgb("#F6B848"); RED_SKY0 = rgb("#401210"); RED_SKY1 = rgb("#B84226")
NIGHT = rgb("#12141F"); MARBLE = (236, 228, 212); FIRE = rgb("#FF8A2A")

def col(c, a=1.0): return skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, a)
def mix(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_out(x, p=3): x = clamp(x); return 1 - (1 - x) ** p
def ease_in(x, p=3): x = clamp(x); return x ** p
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
def lerp(a, b, t): return a + (b - a) * t
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)

# ---------- papier ----------
@functools.lru_cache(maxsize=8)
def paper_tex(w=W, h=H, tint=PAPER, seed=3, fibres=True):
    """Papier crème : bruit basse fréquence (taches), fibres courtes, grain. Retourne une image skia."""
    rng = np.random.default_rng(seed)
    base = np.ones((h, w, 3), np.float32) * np.array(tint, np.float32)
    low = cv2.resize(rng.normal(0, 1, (h // 160 + 2, w // 160 + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    base *= (1 + 0.010 * low)[..., None]
    if fibres:
        f = np.zeros((h, w), np.float32)
        for _ in range(int(w * h / 900)):
            x, y = rng.uniform(0, w), rng.uniform(0, h); a = rng.uniform(0, np.pi); L = rng.uniform(4, 16)
            cv2.line(f, (int(x), int(y)), (int(x + L * np.cos(a)), int(y + L * np.sin(a))), float(rng.uniform(0.3, 1)), 1, cv2.LINE_AA)
        base *= (1 - 0.035 * cv2.GaussianBlur(f, (0, 0), 0.6))[..., None]
    # vignette douce
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    base *= (1 - 0.10 * np.clip(v - 0.3, 0, 1))[..., None]
    return np_to_image(np.clip(base, 0, 255).astype(np.uint8))

def np_to_image(a):
    """numpy RGB ou RGBA uint8 -> skia.Image (alpha non prémultiplié)."""
    if a.shape[2] == 3: a = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
    return skia.Image.fromarray(np.ascontiguousarray(a), colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)

_IMG_CACHE = {}
def asset(name):
    """Charge assets/eng/<name>.png (RGBA) une fois par processus."""
    if name not in _IMG_CACHE:
        a = cv2.imread(os.path.join(ROOT, "assets/eng", name + ".png"), cv2.IMREAD_UNCHANGED)
        if a is None: raise FileNotFoundError(name)
        if a.shape[2] == 4: a = a[..., [2, 1, 0, 3]]
        else: a = a[..., ::-1]
        _IMG_CACHE[name] = np_to_image(a)
    return _IMG_CACHE[name]

SAMPLING = skia.SamplingOptions(skia.CubicResampler.Mitchell())

def draw_img(c, img, cx, cy, scale=1.0, rot=0.0, alpha=1.0, anchor=(0.5, 0.5), blend=None):
    """Pose une image centrée (ou ancrée) en (cx, cy), à l'échelle et rotation données."""
    c.save(); c.translate(cx, cy); c.rotate(rot); c.scale(scale, scale)
    p = skia.Paint(AntiAlias=True); p.setAlphaf(alpha)
    if blend: p.setBlendMode(blend)
    c.drawImageRect(img, skia.Rect.MakeXYWH(-img.width() * anchor[0], -img.height() * anchor[1], img.width(), img.height()), SAMPLING, p)
    c.restore()

def fill_paint(c_, a=1.0): return skia.Paint(AntiAlias=True, Color4f=col(c_, a))
def stroke_paint(c_, w, a=1.0, cap=skia.Paint.kRound_Cap):
    return skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, Color4f=col(c_, a), StrokeCap=cap, StrokeJoin=skia.Paint.kRound_Join)

def glow(c, x, y, r, c_=GOLD, a=0.8):
    """Lueur radiale (halo) — jamais sur un visage (règle de l'auteur)."""
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), r, [col(c_, a), col(c_, a * 0.35), col(c_, 0)], [0, 0.35, 1])
    c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Shader=sh, BlendMode=skia.BlendMode.kPlus))

def vgrad(c, rect, cols, stops=None):
    sh = skia.GradientShader.MakeLinear([skia.Point(rect.left(), rect.top()), skia.Point(rect.left(), rect.bottom())], [col(x) for x in cols], stops)
    c.drawRect(rect, skia.Paint(Shader=sh))

def path_from(pts, close=False):
    p = skia.Path()
    if len(pts) == 0: return p
    p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    if close: p.close()
    return p

def polyline_partial(pts, frac):
    """Portion [0, frac] d'une polyligne (par longueur) + position/direction de la tête."""
    pts = np.asarray(pts, np.float32)
    if len(pts) < 2: return pts, (pts[0] if len(pts) else (0, 0)), (1, 0)
    d = np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1)); L = np.concatenate([[0], np.cumsum(d)])
    target = clamp(frac) * L[-1]; k = np.searchsorted(L, target, side="right") - 1; k = min(k, len(d) - 1)
    f = (target - L[k]) / max(1e-6, d[k]); head = pts[k] + f * (pts[k + 1] - pts[k])
    dirv = (pts[k + 1] - pts[k]) / max(1e-6, d[k])
    return np.vstack([pts[:k + 1], head[None]]), head, dirv

def gold_line(c, pts, frac, width=2.2, t=0.0, trail=True, head=True, energy_=0.5, col_=GOLD):
    """LA LIGNE (9.0) : trait d'or qui se dessine derrière un point de lumière ; traînée lumineuse selon l'énergie."""
    part, hp, _ = polyline_partial(pts, frac)
    if len(part) >= 2:
        pa = path_from(part.tolist())
        if trail:
            gp = stroke_paint(col_, width * (3 + 4 * energy_), 0.18 + 0.25 * energy_)
            gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4 + 6 * energy_))
            c.drawPath(pa, gp)
        c.drawPath(pa, stroke_paint(col_, width))
    if head and frac < 1.0:
        glow(c, float(hp[0]), float(hp[1]), 26 + 30 * energy_, col_, 0.9)
        c.drawCircle(float(hp[0]), float(hp[1]), width * 1.4, fill_paint((255, 244, 214)))
    return hp

# ---------- surface / finition ----------
def new_surface(): return skia.Surface(W, H)

def finish(arr, t, grain=0.03, seed_base=0):
    """Finition numpy : grain discret (±3 %) variable par image. arr : HxWx3 uint8 RGB."""
    rng = np.random.default_rng(seed_base + frame_of(t))
    n = rng.normal(0, grain * 255, (H // 2, W // 2)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)
    return np.clip(arr.astype(np.float32) + n[..., None], 0, 255).astype(np.uint8)

def snapshot_rgb(surface):
    a = surface.makeImageSnapshot().toarray()        # BGRA (vérifié : Skia renvoie du BGRA)
    return np.ascontiguousarray(a[..., [2, 1, 0]])
