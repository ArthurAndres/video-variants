"""Timeline : chaque plan est calé sur des numéros de TEMPS du morceau (analysis.json, début d'attaque).
Un demi-temps s'écrit x.5. Les bornes deviennent des instants exacts (±0 image) via core.beat()."""
import bisect
from engine.core import beat
from engine import shots_a as A
from engine import shots_b as B
from engine import shots_c as C

def S(b0, b1, fn, **kw):
    return dict(b0=b0, b1=b1, fn=fn, **kw)

SHOTS = [
    # --- le hook : une coupe par temps ---
    S(None, 1, A.s_drop),
    S(1, 2, A.s_sun_horizon),
    S(2, 3, A.s_foot),
    S(3, 4, A.s_line_macro),
    S(4, 5, A.s_child_profile),
    S(5, 6, A.s_point_medium),
    S(6, 7, A.s_wide_child),
    S(7, 8, A.s_trunk),
    # --- Éden ---
    S(8, 10, A.s_couple),
    S(10, 11, A.s_fruit_macro),
    S(11, 12, A.s_eve_hand),
    S(12, 13, A.s_adam_profile),
    S(13, 14, A.s_serpent_hidden),
    S(14, 16, A.s_couple_serpent),
    S(16, 17, A.s_bite),
    S(17, 18, A.s_moon),
    S(18, 20, A.s_couple_down),
    S(20, 22, A.s_serpent_coiled),
    S(22, 23, A.s_serpent_eye),
    S(23, 24, A.s_red_sun),
    S(24, 26, A.s_sword),
    S(26, 27, A.s_flames),
    S(27, 29, A.s_couple_away),
    S(29, 30, A.s_fruit_falls),
    # --- symboles, une coupe par demi-temps ---
    S(30, 30.5, A.s_red_cut, kind="bite"),
    S(30.5, 31, A.s_symbol, kind="hourglass"),
    S(31, 31.5, A.s_red_cut, kind="hand"),
    S(31.5, 32, A.s_symbol, kind="wheels"),
    S(32, 32.5, A.s_red_cut, kind="couple"),
    S(32.5, 33, A.s_symbol, kind="tree"),
    S(33, 33.5, A.s_red_cut, kind="serpent"),
    S(33.5, 34, A.s_symbol, kind="triangle"),
    S(34, 34.5, A.s_red_cut, kind="sword"),
    # --- l'encre avale l'écran : noir à la chute (temps 36 = premier temps de la mesure 10) ---
    S(34.5, 36, A.s_ink_flood),
    S(36, 44, A.s_seed),
    # --- Prométhée (creux calme : une coupe toutes les 2 temps) ---
    S(44, 48, B.s_ouroboros),
    S(48, 56, B.s_amphora),
    S(56, 58, B.s_sunrise),
    S(58, 61, B.s_david),
    S(61, 63, B.s_creation),
    S(63, 65, B.s_atlas),
    S(65, 67, B.s_lightning),
    S(67, 69, B.s_stairs),
    S(69, 71, B.s_torch_sun),
    S(71, 73, B.s_torch_close),
    S(73, 75, B.s_statue),
    S(75, 77, B.s_descent),
    # --- l'arrivée des Anunnaki (remplace la caverne de Platon) ---
    S(77, 79, B.s_seal),
    S(79, 81, B.s_anu_descent),
    S(81, 83, B.s_apkallu),
    S(83, 87, B.s_torches),
    S(87, 92, B.s_flip),
    # --- le feu se propage (la musique monte ; temps 92 = premier temps de la mesure 24, impact) ---
    S(92, 93, C.s_net_macro),
    S(93, 94, C.s_bearers),
    S(94, 95, C.s_net_medium),
    S(95, 96, C.s_shadow_gold),
    S(96, 97, C.s_forge_up),
    S(97, 98, C.s_forge_down),
    S(98, 99, C.s_bellows),
    S(99, 100, C.s_pour),
    S(100, 114, C.s_net_recede),
]

for s in SHOTS:
    s["_t0"] = 0.0 if s["b0"] is None else beat(s["b0"])
    s["_t1"] = beat(s["b1"])
    s["_dur"] = s["_t1"] - s["_t0"]
    s["name"] = s["fn"].__name__ + (("_" + s["kind"]) if "kind" in s else "")
_STARTS = [s["_t0"] for s in SHOTS]

def shot_at(t):
    i = bisect.bisect_right(_STARTS, t) - 1
    if i < 0 or t >= SHOTS[i]["_t1"]: return None, 0.0
    return SHOTS[i], t - SHOTS[i]["_t0"]
