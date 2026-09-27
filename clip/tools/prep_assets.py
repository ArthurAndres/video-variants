"""Prépare les références gravées (assets/eng/*.png, RGBA) à partir des photos détourées (assets/masks).
python3 tools/prep_assets.py [nom ...]  ; planche de contrôle : out/review/assets_sheet.jpg"""
import sys, os, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.engrave import engrave, compose, soft_mask, contour_line, hatch, tone_map, main_strokes, INK, GOLD, TERRA, CLAY, MARBLE
from scipy import ndimage as nd

HD = "references/web/hd/"; MK = "assets/masks/"; OUT = "assets/eng/"
os.makedirs(OUT, exist_ok=True)

def load(n):
    img = cv2.imread(HD + n + ".jpg"); m = cv2.imread(MK + n + ".png", 0)
    return img, (m > 127) if m is not None else None

def smooth_mask(m, r=3):
    """Lisse un contour dentelé (chevelures) sans élargir : flou puis seuil."""
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), r) > 0.5

def remove_small(m, n):
    lab, k = nd.label(m); sz = np.bincount(lab.ravel()); keep = np.where(sz >= n)[0]; keep = keep[keep > 0]
    return np.isin(lab, keep)

def save(name, rgba):
    cv2.imwrite(OUT + name + ".png", rgba[..., [2, 1, 0, 3]]); return rgba

def region(m, x0, y0, x1, y1):
    """Garde la partie du masque dans une boîte (fractions)."""
    H, W = m.shape; r = np.zeros_like(m); r[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] = True
    return m & r

A = {}
def job(f): A[f.__name__] = f; return f

@job
def david():
    img, m = load("david_contreplongee"); m = smooth_mask(m, 4)
    r, _, geo = engrave(img, m, 1300, "marble", gamma=1.5, tmax=1.9, pitch=3.0, crop=(0, 0, 1, 0.62), stroke_len=50)
    save("david_marble", r); np.save(OUT + "david_marble_geo.npy", np.array(geo, np.float32))
    # fond : la voûte du musée, gravée à l'encre, atténuée (sans la statue)
    H, W = m.shape; bg = np.ones_like(m); bg[m] = False
    t = tone_map(img, np.ones_like(m), gamma=1.2)
    t = cv2.resize(t, (1300, int(1300 * H / W))); bgm = cv2.resize(bg.astype(np.uint8), (1300, int(1300 * H / W))) > 0
    h = hatch(t, 3.4, 1.6) * bgm
    st = main_strokes(cv2.resize(img, (1300, int(1300 * H / W))), bgm, sigma=2.5, lo=20, hi=50, min_len=80) * 0.8
    save("david_vault", compose([(np.maximum(h, st), INK)], *h.shape))

@job
def discobole():
    img, m = load("discobole_massimo"); m = region(m, 0, 0, 1, 0.80)
    r, _, _ = engrave(img, m, 900, "marble", gamma=1.3, tmax=2.0, stroke_len=50); save("disco_marble", r)
    r, _, _ = engrave(img, m, 900, "blackfig", stroke_len=70); save("disco_blackfig", r)
    r, _, _ = engrave(img, m, 900, "redfig", stroke_len=70); save("disco_redfig", r)
    r, mm, _ = engrave(img, m, 900, "silhouette"); save("disco_sil", r)
    # contour ordonné pour la ligne d'or qui trace le Discobole (coordonnées dans l'image 900 px)
    cnts, _ = cv2.findContours(mm.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cnts, key=len)[:, 0, :].astype(np.float32)
    c = cv2.approxPolyDP(c, 1.2, True)[:, 0, :]
    np.save(OUT + "disco_contour.npy", c)

@job
def atlas():
    img, m = load("atlas_farnese"); m = region(m, 0, 0, 1, 0.86); m = smooth_mask(m, 2)
    r, mm, _ = engrave(img, m, 1000, "marble", gamma=1.4, tmax=2.0, stroke_len=50); save("atlas_marble", r)
    # globe sculpté : cercle ajusté (moindres carrés) sur le contour du haut de la silhouette
    cnts, _ = cv2.findContours(mm.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cnts, key=len)[:, 0, :].astype(np.float64); top = c[c[:, 1] < 0.20 * mm.shape[0]]
    A_ = np.c_[2 * top[:, 0], 2 * top[:, 1], np.ones(len(top))]; b_ = (top ** 2).sum(1)
    cx, cy, k = np.linalg.lstsq(A_, b_, rcond=None)[0]; r0 = np.sqrt(k + cx ** 2 + cy ** 2)
    np.save(OUT + "atlas_globe.npy", np.array([cx, cy, r0], np.float32)); print("globe", cx, cy, r0, mm.shape)

@job
def antinous():
    img, m = load("head_antinous"); m = region(m, 0, 0, 0.86, 0.80); m = smooth_mask(m, 5)
    lab, n = nd.label(m); m = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
    m = nd.binary_fill_holes(m)
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))).astype(bool)
    r, _, _ = engrave(img, m, 1000, "marble", gamma=1.5, tmax=1.9, stroke_len=50)
    h_, w_ = r.shape[:2]; r[:int(0.14 * h_), :int(0.30 * w_), 3] = 0          # le bâton en haut à gauche (fond du musée)
    save("antinous_marble", r)

@job
def creation():
    img, m = load("creation_detail"); H, W = m.shape
    m = region(m, 0, 0, 1, 0.60)
    adam = region(m, 0, 0, 0.45, 1); god = region(m, 0.52, 0, 1, 1)
    lab, n = nd.label(adam); adam = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
    lab, n = nd.label(god); god = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
    # même cadrage pour les deux mains (pas de recadrage individuel) : on grave l'image entière avec chaque masque
    for name, mm, style in (("creation_adam", adam, "terracotta"), ("creation_god", god, "blackgold")):
        r, _, geo = engrave(img, mm, 1400, style, margin=0, crop=None, gamma=1.2, tmax=2.0, stroke_len=30)
        save(name, r); np.save(OUT + name + "_geo.npy", np.array(geo, np.float32))

@job
def eden():
    img, m = load("eden_durer"); m = smooth_mask(m, 2)
    for name, box in (("durer_adam", (0, 0, 0.47, 1)), ("durer_trunk", (0.44, 0, 0.56, 1)), ("durer_eve", (0.53, 0, 1, 1))):
        mm = region(m, *box)
        lab, n = nd.label(mm); mm = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
        r, _, geo = engrave(img, mm, 800, "blackfig", stroke_len=60, canny=(40, 110)); save(name, r)
        np.save(OUT + name + "_geo.npy", np.array(geo, np.float32))
    img, m = load("eden_masaccio"); m = smooth_mask(m, 2)
    r, _, _ = engrave(img, m, 800, "blackfig", stroke_len=60, canny=(25, 70)); save("masaccio_couple", r)
    # macro du pied d'Adam (Masaccio) : vrai profil (talon, voûte, orteils)
    H, W = m.shape; fm = m.copy(); fm[:int(0.87 * H)] = False; fm[:, :int(0.48 * W)] = False; fm[:, int(0.86 * W):] = False
    lab, n = nd.label(fm); fm = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
    r, _, _ = engrave(img, fm, 1100, "silhouette", margin=0.02); save("foot_masaccio", r)
    # gros plan : le serpent dépose le fruit dans la main d'Ève (Dürer), regravé avec les hachures du clip
    img = cv2.imread(HD + "eden_durer_full.jpg"); H, W = img.shape[:2]
    x0, y0, x1, y1 = 0.455, 0.295, 0.655, 0.455
    crop = img[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]
    g = cv2.GaussianBlur(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), (0, 0), 3.5)
    light = g > cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
    light = cv2.morphologyEx(light.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5))).astype(bool)
    light = remove_small(light, 1500)
    r, _, _ = engrave(crop, light, 1400, "marble", margin=0, gamma=1.3, tmax=2.0, pitch=3.0, tone_blur=2.5, stroke_len=150,
                      canny=(25, 60), contour=True, fill=(240, 226, 196))
    # fond : encre sombre, lignes horizontales fines (le tronc)
    bg = np.dstack([np.full(r.shape[:2], c_, np.uint8) for c_ in (34, 24, 18)] + [np.full(r.shape[:2], 255, np.uint8)])
    yy = np.arange(r.shape[0]) % 5 < 1; bg[yy, :, :3] = (60, 44, 32)
    a = r[..., 3:4] / 255.0; out = bg.copy(); out[..., :3] = (r[..., :3] * a + bg[..., :3] * (1 - a)).astype(np.uint8)
    save("durer_hand", out)

@job
def child():
    img, m = load("child_surikov")
    r, _, _ = engrave(img, m, 700, "silhouette"); save("child_back", r)

@job
def pelike():
    img, m = load("torch_pelike")
    r, _, _ = engrave(img, m, 700, "blackfig", stroke_len=25, canny=(40, 120)); save("runner_torch_blackfig", r)
    r, _, _ = engrave(img, m, 700, "silhouette"); save("runner_torch_sil", r)

@job
def parthenon():
    img, m = load("col_parthenon")
    r, _, _ = engrave(img, m, 1600, "ink", gamma=1.2, tmax=2.0, pitch=3.2, stroke_len=60, fill=None)
    # colonnes en marbre sombre sur ciel d'orage : fond gris-bleu + encre
    fm = soft_mask(cv2.resize(m.astype(np.uint8), (r.shape[1], r.shape[0])) > 0)
    base = compose([(fm, (150, 150, 160))], *fm.shape)
    a = r[..., 3:4] / 255.0
    out = base.copy(); out[..., :3] = (r[..., :3] * a + base[..., :3] * (1 - a)).astype(np.uint8)
    save("parthenon", out)

@job
def ouroboros():
    """Gravure fournie (validée dans le test) : formes d'encre pleines, contours lissés par sur-échantillonnage, en or."""
    g = cv2.imread(HD + "ouroboros_test.jpg", 0).astype(np.float32)
    big = cv2.resize(g, (g.shape[1] * 3, g.shape[0] * 3), interpolation=cv2.INTER_CUBIC)
    ink = cv2.GaussianBlur(big, (0, 0), 1.2) < 128
    ink = cv2.morphologyEx(ink.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3))).astype(bool)
    a = soft_mask(ink, 2)
    save("ouroboros_gold", compose([(a, GOLD)], *a.shape))

@job
def anunnaki():
    # recadrages : l'empreinte du sceau seule ; le registre supérieur de la tablette (disque solaire, dieu trônant) ; l'Apkallu entier
    for n, w, crop in (("anu_adda_seal", 1400, (0.34, 0.12, 0.985, 0.90)), ("anu_shamash", 1500, (0.06, 0.02, 0.94, 0.30)),
                       ("anu_apkallu", 1100, (0.0, 0.0, 1.0, 1.0))):
        img = cv2.imread(HD + n + ".jpg"); m = np.ones(img.shape[:2], bool)
        r, _, _ = engrave(img, m, w, "blackgold", margin=0, crop=crop, gamma=1.0, tmax=2.0, stroke_len=40, canny=(30, 90)); save(n + "_gold", r)

@job
def child_profile():
    """Pièce de papier crème découpée : le rendu à l'encre de l'épreuve Badile, forme = figure élargie."""
    src = cv2.imread("out/review/proof_child_profile.png")
    if src is None: print("lancer d'abord tools/proof_child.py"); return
    import importlib.util
    spec = importlib.util.spec_from_file_location("pc", "tools/proof_child.py")
    # on ne ré-exécute pas l'épreuve : on reprend son polygone de figure
    pts = [(110, 185), (170, 120), (260, 94), (360, 88), (450, 100), (520, 125), (560, 175), (576, 250), (580, 330),
           (566, 410), (542, 440), (505, 438), (482, 452), (500, 520), (540, 640), (556, 700), (300, 700), (298, 640),
           (290, 592), (228, 590), (186, 576), (160, 545), (150, 518), (138, 506), (130, 492), (126, 470), (124, 458),
           (100, 446), (94, 436), (104, 412), (116, 382), (114, 350), (110, 322), (106, 296), (110, 265)]
    H, W = src.shape[:2]; m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.array([(x * 2, y * 2) for x, y in pts], np.int32)], 1)
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    a = soft_mask(m > 0)
    rgba = np.dstack([src[..., ::-1], (a * 255).astype(np.uint8)])
    s = 900 / W; rgba = cv2.resize(rgba, (900, int(H * s)), interpolation=cv2.INTER_AREA)
    save("child_profile", rgba)

def sheet():
    import glob
    fs = sorted(glob.glob(OUT + "*.png")); th = 300; tiles = []
    for f in fs:
        a = cv2.imread(f, cv2.IMREAD_UNCHANGED)
        if a is None or a.ndim < 3 or a.shape[2] < 4: continue
        h, w = a.shape[:2]; s = th / max(h, w); a = cv2.resize(a, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA)
        bg = np.full(a.shape[:2] + (3,), (120, 160, 200), np.float32)
        al = a[..., 3:4] / 255.0; im = (a[..., :3] * al + bg * (1 - al)).astype(np.uint8)
        t = np.full((th + 20, th, 3), 40, np.uint8); y = (th - im.shape[0]) // 2; x = (th - im.shape[1]) // 2
        t[y:y + im.shape[0], x:x + im.shape[1]] = im; cv2.putText(t, os.path.basename(f)[:-4], (3, th + 14), 0, 0.42, (255, 255, 255), 1); tiles.append(t)
    while len(tiles) % 6: tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite("out/review/assets_sheet.jpg", np.vstack([np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 85])

if __name__ == "__main__":
    for n in (sys.argv[1:] or list(A)):
        A[n](); print("ok", n)
    sheet()
