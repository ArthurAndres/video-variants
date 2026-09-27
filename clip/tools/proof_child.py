"""Épreuve : l'enfant de profil d'après Badile (NGA, CC0), dans le langage du clip.
- traits : les vrais traits du dessin, rehaussés (passe-haut) puis épurés ;
- cheveux : masse noire dont le bord se casse en vraies mèches du dessin (pas de contour lisse = pas de « casque »),
  reflets clairs = les traits de mèches du dessin ;
- peau : papier nu + hachures horizontales seulement là où le dessin est ombré ;
- silhouette pleine en second rendu (plans en ombre) : NON VALIDÉE (le remplissage déborde), règle des trois échecs.
Contours tracés à la main sur grille (out/review/badile_grid.jpg), coordonnées d'affichage = (pleine − 300) / 2."""
import cv2, numpy as np
from skimage.morphology import remove_small_objects

SRC = "references/web/cand/enf_badile_hd.jpg"
X0, Y0, X1, Y1 = 300, 300, 1500, 1700
PAPER = np.array([200, 228, 240], np.float32)   # #F0E4C8 en BGR
INK = np.array([13, 16, 22], np.float32)        # #16100D en BGR

im = cv2.imread(SRC)[Y0:Y1, X0:X1].astype(np.float32)
H, W = im.shape[:2]
b, g, r = cv2.split(im)
lum = 0.3 * r + 0.59 * g + 0.11 * b
hp = cv2.GaussianBlur(lum, (0, 0), 25) - lum                 # trait = plus sombre que son voisinage
hp = np.clip(hp / np.percentile(hp, 99.5), 0, 1)

def poly_mask(pts, blur=2.0):
    m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.array([(x * 2, y * 2) for x, y in pts], np.int32)], 1)
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), blur) > 0.5

# figure entière (tête + cou), tracée sur le profil réel
figure_pts = [(110, 185), (170, 120), (260, 94), (360, 88), (450, 100), (520, 125), (560, 175), (576, 250), (580, 330),
              (566, 410), (542, 440), (505, 438), (482, 452), (500, 520), (540, 640), (556, 700), (300, 700), (298, 640),
              (290, 592), (228, 590), (186, 576), (160, 545), (150, 518), (138, 506), (130, 492), (126, 470), (124, 458),
              (100, 446), (94, 436), (104, 412), (116, 382), (114, 350), (110, 322), (106, 296), (110, 265)]
# chevelure : bord supérieur = contour de la figure ; bord inférieur = bas des mèches et de la frange, relevé sur le dessin
hair_pts = [(110, 185), (170, 120), (260, 94), (360, 88), (450, 100), (520, 125), (560, 175), (576, 250), (580, 330),
            (566, 410), (542, 440), (505, 438), (486, 418), (468, 398), (440, 380), (410, 374), (392, 356), (370, 346),
            (344, 340), (318, 322), (290, 308), (262, 300), (230, 296), (196, 292), (160, 290), (130, 292), (112, 290), (108, 262)]
fig_poly = poly_mask(figure_pts)
hair_poly = poly_mask(hair_pts)
# calage sur les vrais traits : le fond est rempli depuis l'extérieur et s'arrête sur les traits du dessin ;
# le polygone ne sert que de garde-fou (noyau sûr + zone de recherche)
from scipy import ndimage as nd
barrier = cv2.dilate((hp > 0.30).astype(np.uint8), np.ones((5, 5))).astype(bool)
zone = cv2.dilate(fig_poly.astype(np.uint8), np.ones((41, 41))).astype(bool)
lab, _ = nd.label(~barrier)
seeds = np.unique(lab[(~zone) & (lab > 0)])
background = np.isin(lab, seeds) & (lab > 0)
core_fig = cv2.erode(fig_poly.astype(np.uint8), np.ones((25, 25))).astype(bool)
fig = (zone & ~background) | core_fig
fig = nd.binary_fill_holes(fig)
fig = cv2.morphologyEx(fig.astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7))).astype(bool)
lab2, n2 = nd.label(fig); fig = lab2 == (np.argmax(np.bincount(lab2.ravel())[1:]) + 1)

# traits épurés, limités à la figure (légèrement élargie) : le fond hachuré de Badile disparaît
lines = np.clip((hp - 0.28) / 0.45, 0, 1)
keep = remove_small_objects(lines > 0.35, max_size=90)
lines = lines * keep * cv2.dilate(fig.astype(np.uint8), np.ones((15, 15))).astype(np.float32)

# chevelure : noyau plein + bord fait des mèches réelles
core = cv2.erode(hair_poly.astype(np.uint8), np.ones((31, 31))).astype(bool)
band = cv2.dilate(hair_poly.astype(np.uint8), np.ones((11, 11))).astype(bool) & ~core
strands = cv2.dilate((hp > 0.30).astype(np.uint8), np.ones((3, 3))).astype(bool)
hair = core | (band & strands) | (hair_poly & (cv2.GaussianBlur(hp, (0, 0), 3) > 0.12))
hair = cv2.morphologyEx(hair.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3))).astype(np.float32)
hair = cv2.GaussianBlur(hair, (0, 0), 0.8)

# ombrage : assombrissement basse fréquence du dessin, à l'intérieur de la figure seulement
shade = cv2.GaussianBlur(lum, (0, 0), 40) - cv2.GaussianBlur(lum, (0, 0), 8)
shade = np.clip(shade / np.percentile(shade[fig], 97), 0, 1) * fig
yy = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
bandh = np.abs(((yy / 6.0) % 1.0) - 0.5) * 2
width = np.clip(shade * 0.7, 0, 0.6)
hatch = np.clip((width - bandh) * 5 + 0.5, 0, 1) * (width > 0.04)

def paper():
    rng = np.random.default_rng(1)
    return (np.ones((H, W, 3), np.float32) * PAPER) * (1 + cv2.GaussianBlur(rng.normal(0, 0.03, (H, W)).astype(np.float32), (0, 0), 0.7))[..., None]

# rendu 1 : encre
out = paper()
body = 1 - hair
ink = np.clip(lines * body + hatch * 0.6 * body, 0, 1)
out = out * (1 - ink[..., None]) + INK * ink[..., None]
refl = np.clip((hp - 0.18) / 0.30, 0, 1) * cv2.erode(core.astype(np.uint8), np.ones((5, 5))).astype(np.float32) * 0.9
hair_col = INK * (1 - refl[..., None]) + PAPER * refl[..., None]
out = out * (1 - hair[..., None]) + hair_col * hair[..., None]
out = np.clip(out, 0, 255).astype(np.uint8)

# rendu 2 : silhouette pleine (figure ∪ cheveux), bords de mèches conservés
sil = np.clip(np.maximum(cv2.GaussianBlur(fig.astype(np.float32), (0, 0), 0.8), hair), 0, 1)
out2 = paper(); out2 = out2 * (1 - sil[..., None]) + INK * sil[..., None]
out2 = np.clip(out2, 0, 255).astype(np.uint8)

cv2.imwrite("out/review/proof_child_profile.png", out)
cv2.imwrite("out/review/proof_child_silhouette.png", out2)
s = lambda a: cv2.resize(a.astype(np.uint8), (W // 2, H // 2), interpolation=cv2.INTER_AREA)
cv2.imwrite("out/review/proof_child_side.jpg", np.hstack([s(im), s(out)]), [cv2.IMWRITE_JPEG_QUALITY, 88])
print("ok")
