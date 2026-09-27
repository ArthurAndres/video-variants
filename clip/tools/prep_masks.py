"""Détourage des références (annexe A.3) : YOLO seg (masque de départ) -> GrabCut initialisé par ce masque.
python3 tools/prep_masks.py [nom ...]   -> assets/masks/<nom>.png + out/review/masks_<lot>.jpg (superposition)
Les cas particuliers (fond uni, couleur) sont réglés par la table RECIPES."""
import sys, os, cv2, numpy as np
from scipy import ndimage as nd

HD = "references/web/hd/"
OUT = "assets/masks/"
os.makedirs(OUT, exist_ok=True)

_yolo = None
def yolo_masks(img, classes=(0,), conf=0.15):
    """Masques d'instances (personnes par défaut) à la taille de l'image."""
    global _yolo
    if _yolo is None:
        from ultralytics import YOLO
        _yolo = YOLO("models/yolo11x-seg.pt")
    r = _yolo.predict(img, conf=conf, classes=list(classes), retina_masks=True, verbose=False, imgsz=1280)[0]
    if r.masks is None: return []
    ms = r.masks.data.cpu().numpy() > 0.5
    return [(m, float(c)) for m, c in zip(ms, r.boxes.conf.cpu().numpy())]

def grabcut(img, init, iters=6, band=12):
    """GrabCut initialisé par un masque : intérieur sûr = érodé, extérieur sûr = hors dilaté."""
    m = np.full(init.shape, cv2.GC_PR_BGD, np.uint8)
    k = np.ones((band, band), np.uint8)
    m[cv2.dilate(init.astype(np.uint8), k) == 0] = cv2.GC_BGD
    m[init > 0] = cv2.GC_PR_FGD
    m[cv2.erode(init.astype(np.uint8), k) > 0] = cv2.GC_FGD
    bg, fg = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(img, m, None, bg, fg, iters, cv2.GC_INIT_WITH_MASK)
    return (m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)

def clean(m, min_hole=400, keep="largest"):
    m = nd.binary_fill_holes(m) if min_hole is None else m
    lab, n = nd.label(m)
    if n == 0: return m
    sizes = np.bincount(lab.ravel()); sizes[0] = 0
    if keep == "largest": m = lab == np.argmax(sizes)
    # petits trous (bruit) bouchés, grands trous (vides réels) conservés
    holes = nd.binary_fill_holes(m) & ~m
    hl, hn = nd.label(holes)
    if hn:
        hs = np.bincount(hl.ravel()); small = np.where(hs < min_hole)[0]; small = small[small > 0]
        m = m | np.isin(hl, small)
    return m

def person(name, pick=0, union=False, gc=True, band=12):
    img = cv2.imread(HD + name + ".jpg")
    ms = yolo_masks(img)
    if not ms: raise SystemExit(f"{name}: aucune personne détectée")
    ms.sort(key=lambda x: -x[0].sum())
    m = np.any([x[0] for x in ms[: (union if union else 1)]], axis=0) if union else ms[pick][0]
    if gc: m = grabcut(img, m, band=band)
    return img, m

def rect_gc(name, rect, iters=8):
    """GrabCut initialisé par un rectangle (x0, y0, x1, y1 en fractions de l'image)."""
    img = cv2.imread(HD + name + ".jpg"); h, w = img.shape[:2]
    r = (int(rect[0] * w), int(rect[1] * h), int((rect[2] - rect[0]) * w), int((rect[3] - rect[1]) * h))
    m = np.zeros((h, w), np.uint8); bg, fg = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(img, m, r, bg, fg, iters, cv2.GC_INIT_WITH_RECT)
    return img, (m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)

def yolo_multi(img, sizes=(640, 960, 1280, 1600), top=2):
    """Union des masques YOLO sur plusieurs tailles d'entrée (le modèle est instable d'une taille à l'autre)."""
    acc = np.zeros(img.shape[:2], bool)
    for sz in sizes:
        global _yolo
        if _yolo is None:
            from ultralytics import YOLO
            _yolo = YOLO("models/yolo11x-seg.pt")
        r = _yolo.predict(img, conf=0.15, classes=[0], retina_masks=True, verbose=False, imgsz=sz)[0]
        if r.masks is None: continue
        ms = sorted(r.masks.data.cpu().numpy() > 0.5, key=lambda m: -m.sum())[:top]
        for m in ms: acc |= m
    return acc

def mixed(name, top=1, thr_dark=False, band=16, cut_bottom=None):
    """Départ = union YOLO multi-tailles (∪ seuil fond sombre si demandé), puis GrabCut."""
    img = cv2.imread(HD + name + ".jpg")
    init = yolo_multi(img, top=top)
    if thr_dark:
        g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (0, 0), 3)
        init |= g > cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
    if cut_bottom: init[int(cut_bottom * img.shape[0]):] = False
    return img, grabcut(img, clean(init), band=band)

def hsv_mask(name, fn, band=10, gc=True, open_k=5):
    """Masque par couleur (fonction de H, S, V en uint8 OpenCV), nettoyé, puis GrabCut optionnel."""
    img = cv2.imread(HD + name + ".jpg"); h, s_, v = cv2.split(cv2.cvtColor(img, cv2.COLOR_BGR2HSV))
    m = fn(h.astype(int), s_.astype(int), v.astype(int))
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((open_k, open_k))).astype(bool)
    return img, (grabcut(img, m, band=band) if gc else m)

def lab_skin(name, boxes, thr=None, band=14):
    """Peau chaude contre plâtre gris : canal a* (Lab) seuillé (Otsu dans les boîtes), puis GrabCut. boxes en fractions."""
    img = cv2.imread(HD + name + ".jpg"); H, W = img.shape[:2]
    a = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[..., 1], (0, 0), 1.5)
    out = np.zeros((H, W), bool)
    for x0, y0, x1, y1 in boxes:
        sl = (slice(int(y0 * H), int(y1 * H)), slice(int(x0 * W), int(x1 * W)))
        sub = a[sl]; t = thr or cv2.threshold(sub, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
        m = np.zeros((H, W), bool); m[sl] = sub > t
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9))).astype(bool)
        m = clean(m)
        box = np.zeros((H, W), bool); box[sl] = True
        out |= grabcut(img, m, band=band) & box
    return img, out

def dark_bg(name, thr=None, blur=3):
    """Sujet clair sur fond sombre : seuil d'Otsu sur la luminance lissée, puis GrabCut."""
    img = cv2.imread(HD + name + ".jpg"); g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (0, 0), blur)
    t = thr if thr is not None else cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
    return img, grabcut(img, clean(g > t), band=10)

RECIPES = {
    # nom: (fonction, kwargs, post-traitement)
    # YOLO est instable sur statues et fresques (jambes coupées selon imgsz) : seuil sur fond sombre / rectangle
    "david_contreplongee": (mixed, {}),
    "discobole_massimo": (mixed, {"thr_dark": True}),
    "atlas_farnese": (dark_bg, {}),
    "head_antinous": (rect_gc, {"rect": (0.12, 0.12, 0.86, 0.99)}),
    "eden_masaccio": (mixed, {"top": 2}),
    "child_surikov": (mixed, {}),
    "eden_durer": (mixed, {"top": 2}),
    # vase à figures rouges : la figure orange sur le vernis noir
    "torch_pelike": (hsv_mask, {"fn": lambda h, s, v: (h >= 5) & (h <= 22) & (s > 110) & (v > 110)}),
    # mains de la Création : peau chaude et saturée contre plâtre gris (annexe A.4)
    "creation_detail": (lab_skin, {"boxes": [(0.0, 0.20, 0.47, 0.52), (0.47, 0.14, 1.0, 0.57)]}),
    # colonnes : tout ce qui n'est pas le ciel bleu
    "col_parthenon": (hsv_mask, {"fn": lambda h, s, v: ~((h > 95) & (h < 125) & (s > 60)), "gc": False}),
}

def overlay(img, m):
    o = img.copy(); o[~m] = (o[~m] * 0.25).astype(np.uint8)
    cnts, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(o, cnts, -1, (0, 0, 255), 2)
    return o

def sheet(items, path, th=420):
    tiles = []
    for name, img, m in items:
        o = overlay(img, m); h, w = o.shape[:2]; s = th / max(h, w); o = cv2.resize(o, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        t = np.full((th + 22, th, 3), 30, np.uint8); y = (th - o.shape[0]) // 2; x = (th - o.shape[1]) // 2
        t[y:y + o.shape[0], x:x + o.shape[1]] = o; cv2.putText(t, name, (4, th + 16), 0, 0.5, (255, 255, 255), 1); tiles.append(t)
    while len(tiles) % 4: tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(path, np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]), [cv2.IMWRITE_JPEG_QUALITY, 85])

if __name__ == "__main__":
    names = sys.argv[1:] or list(RECIPES)
    items = []
    for n in names:
        fn, kw = RECIPES[n][:2]
        try: img, m = fn(n, **kw)
        except SystemExit as e: print("ÉCHEC", e); continue
        m = clean(m, keep=None if n in ("creation_detail", "col_parthenon") else "largest")
        cv2.imwrite(OUT + n + ".png", (m * 255).astype(np.uint8))
        items.append((n, img, m)); print(n, m.shape, f"{m.mean():.3f}")
    sheet(items, "out/review/masks_" + ("all" if not sys.argv[1:] else "lot") + ".jpg")
