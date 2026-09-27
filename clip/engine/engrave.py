"""Gravure d'une référence réelle (annexe A.3) : modelé OBSERVÉ -> hachures horizontales + traits principaux + contour.
Produit une image RGBA (uint8) prête à poser dans le monde, nette à la taille prévue (échelle `scale`).

Styles :
  marble    : fond marbre clair, hachures et traits à l'encre
  terracotta: fond terre cuite, hachures encre (Adam de la Création)
  blackgold : fond noir, lignes d'or calculées sur les LUMIÈRES (ton inversé)
  blackfig  : figure noire pleine + incisions couleur argile (traits principaux seulement) — vase à figures noires
  redfig    : figure argile + traits noirs, fond transparent — vase à figures rouges
  silhouette: noir plein
  ink       : hachures + traits à l'encre sans fond (sur papier)
"""
import cv2, numpy as np
from skimage.morphology import skeletonize, remove_small_objects

INK = (22, 16, 13)
CREAM = (240, 228, 200)
MARBLE = (236, 228, 212)
TERRA = (198, 108, 60)
CLAY = (190, 96, 48)
GOLD = (246, 184, 72)

def _prep(img, mask, width, margin=0.03, crop=None):
    """Recadre sur le masque (+ marge) puis redimensionne à `width` px de large."""
    if crop is not None:
        x0, y0, x1, y1 = crop
        H, W = mask.shape
        img = img[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]
        mask = mask[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]
    ys, xs = np.where(mask)
    H, W = mask.shape
    m = int(margin * max(H, W))
    x0, x1 = max(0, xs.min() - m), min(W, xs.max() + m + 1)
    y0, y1 = max(0, ys.min() - m), min(H, ys.max() + m + 1)
    img, mask = img[y0:y1, x0:x1], mask[y0:y1, x0:x1]
    s = width / img.shape[1]
    size = (width, max(1, int(round(img.shape[0] * s))))
    img = cv2.resize(img, size, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    mask = cv2.resize(mask.astype(np.float32), size, interpolation=cv2.INTER_AREA) > 0.5
    return img, mask, (x0, y0, s)

def tone_map(img, mask, lo=2, hi=98, blur=0.8, gamma=1.0):
    """Ton 0 (lumière) .. 1 (ombre), normalisé par percentiles DANS le masque."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), blur)
    vals = g[mask] if mask.any() else g.ravel()
    a, b = np.percentile(vals, lo), np.percentile(vals, hi)
    t = np.clip((b - g) / max(1e-3, b - a), 0, 1)
    return t ** gamma

def hatch(tone, pitch=3.0, tmax=2.0, tmin=0.0, ss=3, angle=0.0, wobble=0.0, seed=0):
    """Rubans horizontaux dont l'épaisseur suit le ton (enflent dans l'ombre). Anticrénelé par sur-échantillonnage."""
    H, W = tone.shape
    T = cv2.resize(tone, (W * ss, H * ss), interpolation=cv2.INTER_LINEAR)
    yy, xx = np.mgrid[0:H * ss, 0:W * ss].astype(np.float32) / ss
    if angle:
        a = np.deg2rad(angle); yy = yy * np.cos(a) + xx * np.sin(a)
    if wobble:
        rng = np.random.default_rng(seed)
        n = cv2.resize(rng.normal(0, 1, (max(2, H // 40), max(2, W // 40))).astype(np.float32), (W * ss, H * ss), interpolation=cv2.INTER_CUBIC)
        yy = yy + wobble * n
    d = np.abs(((yy / pitch) % 1.0) - 0.5) * pitch          # distance au centre de la ligne (px)
    th = tmin + (tmax - tmin) * T
    ink = np.clip((th / 2 - d) * ss + 0.5, 0, 1) * (T > 0.02)
    return cv2.resize(ink, (W, H), interpolation=cv2.INTER_AREA)

def main_strokes(img, mask, sigma=2.0, lo=30, hi=80, min_len=40, width=1.1, ss=3):
    """Traits principaux : Canny sur image floutée, squelette, composantes courtes écartées (sinon « gribouillis »)."""
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (0, 0), sigma)
    e = cv2.Canny(g, lo, hi) > 0
    e &= cv2.erode(mask.astype(np.uint8), np.ones((5, 5))).astype(bool)
    e = skeletonize(e)
    e = remove_small_objects(e, max_size=min_len, connectivity=2)
    return draw_mask_lines(e, width, ss)

def draw_mask_lines(sk, width, ss=3):
    H, W = sk.shape
    big = cv2.resize(sk.astype(np.uint8), (W * ss, H * ss), interpolation=cv2.INTER_NEAREST)
    r = max(1, int(round(width * ss / 2)))
    big = cv2.dilate(big, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    return cv2.resize(big.astype(np.float32), (W, H), interpolation=cv2.INTER_AREA)

def contour_line(mask, width=1.4, ss=3):
    H, W = mask.shape
    big = cv2.resize(mask.astype(np.uint8), (W * ss, H * ss), interpolation=cv2.INTER_LINEAR)
    big = cv2.GaussianBlur(big.astype(np.float32), (0, 0), ss * 0.6) > 0.5
    cnts, _ = cv2.findContours(big.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    out = np.zeros((H * ss, W * ss), np.uint8)
    cv2.drawContours(out, cnts, -1, 1, max(1, int(round(width * ss))), lineType=cv2.LINE_AA)
    return cv2.resize(out.astype(np.float32), (W, H), interpolation=cv2.INTER_AREA)

def soft_mask(mask, ss=3):
    H, W = mask.shape
    big = cv2.resize(mask.astype(np.uint8), (W * ss, H * ss), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    big = (cv2.GaussianBlur(big, (0, 0), ss * 0.6) > 0.5).astype(np.float32)
    return cv2.resize(big, (W, H), interpolation=cv2.INTER_AREA)

def compose(layers, H, W):
    """layers : liste de (alpha HxW, couleur RGB). Retourne RGBA uint8 (non prémultiplié)."""
    rgb = np.zeros((H, W, 3), np.float32); a = np.zeros((H, W), np.float32)
    for al, col in layers:
        al = np.clip(al, 0, 1)
        rgb = rgb * (1 - al[..., None]) + np.array(col, np.float32) * al[..., None]
        a = a + al * (1 - a)
    out = np.dstack([np.clip(rgb, 0, 255), np.clip(a * 255, 0, 255)]).astype(np.uint8)
    return out

def engrave(img, mask, width, style="marble", pitch=3.0, tmax=2.1, gamma=1.0, strokes=True, stroke_len=40,
            contour=True, crop=None, margin=0.03, fill=None, line_col=None, wobble=0.0, tone_blur=0.8, canny=(30, 80)):
    img, mask, geo = _prep(img, mask, width, margin, crop)
    H, W = mask.shape
    t = tone_map(img, mask, blur=tone_blur, gamma=gamma)
    fm = soft_mask(mask)
    if style == "blackgold":
        h = hatch(1 - t, pitch, tmax * 0.8, wobble=wobble) * fm
        st = main_strokes(img, mask, lo=canny[0], hi=canny[1], min_len=stroke_len, width=0.9) * 0.6 if strokes else 0
        layers = [(fm, fill or INK), (np.maximum(h, st), line_col or GOLD)]
    elif style == "blackfig":
        st = main_strokes(img, mask, lo=canny[0], hi=canny[1], min_len=stroke_len, width=1.0) if strokes else np.zeros_like(fm)
        layers = [(fm, fill or INK), (st * fm, line_col or TERRA)]
    elif style == "redfig":
        st = main_strokes(img, mask, lo=canny[0], hi=canny[1], min_len=stroke_len, width=1.0) if strokes else np.zeros_like(fm)
        layers = [(fm, fill or CLAY), (st * fm, line_col or INK)]
        if contour: layers.append((contour_line(mask, 1.2), line_col or INK))
    elif style == "silhouette":
        layers = [(fm, fill or INK)]
    else:
        h = hatch(t, pitch, tmax, wobble=wobble) * fm
        layers = []
        if style != "ink": layers.append((fm, fill or (TERRA if style == "terracotta" else MARBLE)))
        layers.append((h, line_col or INK))
        if strokes: layers.append((main_strokes(img, mask, lo=canny[0], hi=canny[1], min_len=stroke_len) * 0.85, line_col or INK))
        if contour: layers.append((contour_line(mask), line_col or INK))
    return compose(layers, H, W), mask, geo
