#!/usr/bin/env python3
"""Mesure d'une disposition par différence de différences sur deux mots fixes.

Pour chaque début de situation et chaque cadre :

    delta(debut) = logP(mot A | debut + cadre) - logP(mot B | debut + cadre)

Statistiques, appariées par domaine (n = 12) :

    K = delta(C1) - delta(C6)   contrôle de compétence, doit être > 0 avec t > 2
    S = delta(C2) - delta(C5)   S > 0 penchant « fondement intérieur »,
                                S < 0 penchant « vérification publique »

Toute propriété propre aux deux mots apparaît avec des signes opposés dans
chaque différence et s'annule exactement. On ne compare jamais deux phrases
différentes.

Usage :
    python measure.py --dry                      # faux scoreur, vérifie les maths
    python measure.py --model Qwen/Qwen2.5-0.5B
    python measure.py --model Qwen/Qwen2.5-0.5B --fallback Qwen/Qwen2.5-1.5B
"""

import argparse
import hashlib
import json
import math
import statistics
import sys

# --------------------------------------------------------------------------
# Matériel de mesure — à garder identique d'une mesure à l'autre.

DOMAINS = [
    ("whether the arch will stand", "how the thrust runs through it", "a load test"),
    ("whether the vaccine batch is viable", "what the titre curve implies", "a potency assay"),
    ("whether the sauce will split", "what the emulsion is holding", "a trial spoonful"),
    ("whether the primer will adhere", "what the old surface has absorbed", "a tape pull"),
    ("whether the turbine is out of balance", "where the vibration peaks in a cycle", "a spectrum reading"),
    ("whether the beech is unsafe", "how the crown answered the lean", "a resistance drill"),
    ("whether the chimney draws", "how the flue changes section", "a smoke test"),
    ("whether the well is running dry", "how the level recovers overnight", "a pump trial"),
    ("whether the seam will weep", "how the fold sits under pressure", "a pressure test"),
    ("whether the slab has cured", "how it sounds under a hammer", "a crush test"),
    ("whether the plot holds", "where the middle act stops paying", "a script reading"),
    ("whether the hull needs stripping", "how the paint lifted from the laminate", "a moisture meter"),
]

TEMPLATES = {
    "C1": "{Objet} is in question. {Fondement} is clear, and {controle} can be run.",
    "C2": "{Objet} is in question. {Fondement} is clear, while {controle} is out of the question here.",
    "C3": "{Objet} is in question. Working out {fondement} would take a week, while {controle} can be run today.",
    "C4": "{Objet} is in question. Working out {fondement} would take a week, and {controle} is unavailable for this.",
    "C5": "{Objet} is in question. {Fondement} is beyond reach, while {controle} can be run.",
    "C6": "{Objet} is in question. {Fondement} is beyond reach, and {controle} is unavailable.",
}
CASES = list(TEMPLATES)

# (cadre, mot A = « tranché », mot B = « ouvert »)
FRAMES = [
    ("So the matter is", "settled", "open"),
    ("So I would call it", "right", "unproven"),
    ("So the question is", "closed", "live"),
]

T_THRESHOLD = 2.0


def cap(s):
    return s[:1].upper() + s[1:]


def debut(case, domain):
    objet, fondement, controle = domain
    return TEMPLATES[case].format(
        Objet=cap(objet), Fondement=cap(fondement),
        fondement=fondement, controle=controle,
    )


def prefix(case, domain, frame):
    return f"{debut(case, domain)} {frame}"


# --------------------------------------------------------------------------
# Scoreurs : score(prefix, word) -> logP(" " + word | prefix), en nats.

class HFScorer:
    """Log-probabilité exacte d'un mot (somme sur ses tokens) après un préfixe."""

    def __init__(self, model_name):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.float32)
        self.model.eval()
        self.name = model_name

    def score(self, prefix_text, word):
        torch = self.torch
        p_ids = self.tok(prefix_text, add_special_tokens=False)["input_ids"]
        full_ids = self.tok(prefix_text + " " + word, add_special_tokens=False)["input_ids"]
        # Le mot doit s'ajouter en tokens propres, sans refondre la fin du préfixe.
        if full_ids[:len(p_ids)] != p_ids:
            raise ValueError(f"tokenisation non séparable : {prefix_text!r} + {word!r}")
        w_ids = full_ids[len(p_ids):]
        ids = torch.tensor([full_ids])
        with torch.no_grad():
            logits = self.model(ids).logits[0]
        logp = torch.log_softmax(logits.double(), dim=-1)
        start = len(p_ids)
        return sum(logp[start + i - 1, t].item() for i, t in enumerate(w_ids))


def _unit(*parts):
    """Nombre pseudo-aléatoire déterministe dans [-1, 1) à partir d'une clé."""
    h = hashlib.sha256("\x1f".join(parts).encode()).digest()
    return int.from_bytes(h[:8], "big") / 2**63 - 1.0


class FakeScorer:
    """Faux scoreur déterministe qui plante un effet connu.

    logP(mot) = nuisance(mot) + nuisance(mot, domaine) + nuisance(mot, cadre)
                + effet planté + bruit(cas, domaine, mot)

    Les nuisances ne dépendent pas du cas : elles doivent disparaître de K
    et S. L'effet planté vaut, sur delta = A - B :
        C1 : +K/2   C6 : -K/2   C2 : +S/2   C5 : -S/2   (C3, C4 : 0)
    Il ne lit que le texte du préfixe pour reconnaître le cas.
    """

    MARKERS = [  # ordre important : C3/C4 avant les autres
        ("C3", "would take a week, while"),
        ("C4", "would take a week, and"),
        ("C2", "is clear, while"),
        ("C1", "is clear, and"),
        ("C5", "is beyond reach, while"),
        ("C6", "is beyond reach, and"),
    ]

    def __init__(self, k_true, s_true, noise=0.15):
        self.k, self.s, self.noise = k_true, s_true, noise
        self.a_words = {a for _, a, _ in FRAMES}
        self.name = f"fake(K={k_true}, S={s_true})"

    def _case(self, text):
        for case, marker in self.MARKERS:
            if marker in text:
                return case
        raise ValueError(f"cas introuvable : {text!r}")

    def score(self, prefix_text, word):
        case = self._case(prefix_text)
        body, frame = prefix_text.rsplit(". ", 1)
        situation = body.split(" is in question.")[0]
        base = -3.0 - 0.4 * len(word) + 2.0 * _unit("w", word)        # fréquence, longueur
        base += 1.5 * _unit("wd", word, situation)                        # mot × domaine
        base += 1.0 * _unit("wf", word, frame)                            # mot × cadre
        base += self.noise * _unit("n", case, situation, word, frame)     # bruit
        planted = {"C1": self.k, "C6": -self.k, "C2": self.s, "C5": -self.s}.get(case, 0.0) / 2
        return base + (planted if word in self.a_words else 0.0)


# --------------------------------------------------------------------------
# Calcul

def tstat(xs):
    n = len(xs)
    m = statistics.fmean(xs)
    sd = statistics.stdev(xs)
    t = m / (sd / math.sqrt(n)) if sd > 0 else math.copysign(math.inf, m) if m else 0.0
    return m, sd, t


def measure(scorer):
    """Renvoie deltas[frame][case] = liste de 12 deltas, et stats par cadre."""
    out = {}
    for frame, a, b in FRAMES:
        deltas = {c: [] for c in CASES}
        for case in CASES:
            for d in DOMAINS:
                p = prefix(case, d, frame)
                deltas[case].append(scorer.score(p, a) - scorer.score(p, b))
        k = [x - y for x, y in zip(deltas["C1"], deltas["C6"])]
        s = [x - y for x, y in zip(deltas["C2"], deltas["C5"])]
        out[frame] = {"words": (a, b), "deltas": deltas, "K": tstat(k), "S": tstat(s)}
    return out


def report(name, res):
    print(f"\n=== {name} ===")
    print("\nDelta moyen par case (nats, moyenne sur 12 domaines ; ± écart-type)")
    head = "cadre".ljust(24) + "".join(c.rjust(14) for c in CASES)
    print(head)
    for frame, r in res.items():
        a, b = r["words"]
        row = f"{frame} [{a}/{b}]"[:24].ljust(24)
        for c in CASES:
            xs = r["deltas"][c]
            row += f"{statistics.fmean(xs):+7.2f}±{statistics.stdev(xs):4.2f}".rjust(14)
        print(row)
    print("\nK = delta(C1) - delta(C6)   S = delta(C2) - delta(C5)   (n = 12, ddl = 11)")
    print("cadre".ljust(24) + "K".rjust(9) + "t(K)".rjust(8) + "S".rjust(9) + "t(S)".rjust(8) + "  K passe ?")
    for frame, r in res.items():
        km, _, kt = r["K"]
        sm, _, st = r["S"]
        ok = "oui" if km > 0 and kt > T_THRESHOLD else "NON"
        print(frame.ljust(24) + f"{km:+9.3f}{kt:+8.2f}{sm:+9.3f}{st:+8.2f}  {ok}")


def k_passes(res):
    return all(r["K"][0] > 0 and r["K"][2] > T_THRESHOLD for r in res.values())


def to_json(res):
    return {f: {"words": r["words"], "deltas": r["deltas"],
                "K": dict(zip(("mean", "sd", "t"), r["K"])),
                "S": dict(zip(("mean", "sd", "t"), r["S"]))} for f, r in res.items()}


# --------------------------------------------------------------------------

def dry():
    """Plante des effets connus et vérifie que K et S les retrouvent."""
    ok = True
    for k_true, s_true in [(2.0, 0.8), (2.0, -0.8), (2.0, 0.0), (0.0, 0.8)]:
        res = measure(FakeScorer(k_true, s_true))
        report(f"dry  K planté = {k_true:+}, S planté = {s_true:+}", res)
        for frame, r in res.items():
            for stat, true in (("K", k_true), ("S", s_true)):
                m, _, t = r[stat]
                good = abs(m - true) < 0.15
                if true != 0:
                    good &= math.copysign(1, t) == math.copysign(1, true) and abs(t) > T_THRESHOLD
                if not good:
                    ok = False
                    print(f"  ÉCHEC {frame} {stat}: estimé {m:+.3f} (t={t:+.2f}), planté {true:+}")
    # Nuisances pures (aucun effet planté, aucun bruit) : K et S doivent valoir 0 exactement.
    res = measure(FakeScorer(0.0, 0.0, noise=0.0))
    for frame, r in res.items():
        for stat in ("K", "S"):
            if abs(r[stat][0]) > 1e-9:
                ok = False
                print(f"  ÉCHEC annulation {frame} {stat}: {r[stat][0]!r}")
    print("\nDRY :", "OK — K et S retrouvent les effets plantés, nuisances annulées"
          if ok else "ÉCHEC")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry", action="store_true", help="faux scoreur déterministe, ne télécharge rien")
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B")
    ap.add_argument("--fallback", default=None, help="modèle à essayer si K échoue")
    ap.add_argument("--json", default=None, help="écrit les résultats bruts dans ce fichier")
    ap.add_argument("--show-items", action="store_true", help="affiche les 72 débuts")
    args = ap.parse_args()

    if args.show_items:
        for c in CASES:
            for d in DOMAINS:
                print(c, debut(c, d))
        return 0
    if args.dry:
        return 0 if dry() else 1

    results = {}
    for name in [args.model] + ([args.fallback] if args.fallback else []):
        res = measure(HFScorer(name))
        report(name, res)
        results[name] = to_json(res)
        if k_passes(res):
            print(f"\nK passe sur les trois cadres pour {name} : S est interprétable.")
            break
        print(f"\nK échoue sur au moins un cadre pour {name} : ne pas interpréter S.")
    if args.json:
        with open(args.json, "w") as f:
            json.dump(results, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
