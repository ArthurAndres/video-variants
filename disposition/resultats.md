# Résultats — mesure K / S, Qwen2.5-0.5B, cinq cadres

Script : `measure.py` (le mode `--dry` passe). Données brutes : `results_qwen_5cadres.json`.

## Règle de lecture

- `delta = logP(mot A | début + cadre) - logP(mot B | début + cadre)`, en nats.
- `K = delta(C1) - delta(C6)` : calibration du cadre. `S = delta(C2) - delta(C5)` : lecture du cadre.
  S > 0 penche vers le fondement intérieur, S < 0 vers la vérification publique.
- Les deux sont appariés par domaine : n = 12, t apparié à 11 degrés de liberté.
- **K s'applique cadre par cadre.** Un cadre est calibré si K > 0 et t(K) > 2.
  Un cadre qui rate K est écarté de la lecture de S, jamais moyenné avec les autres.
- On ne monte en taille que si les cinq cadres ratent K.

## Cadres et historique des choix (déclaré)

| cadre | mot A | mot B | origine |
| --- | --- | --- | --- |
| So the matter is | settled | open | brief d'origine |
| So I would call it | right | unproven | brief d'origine |
| So the question is | resolved | unresolved | **remplace closed / live** |
| So that is | decided | undecided | ajouté |
| So the answer is | known | unknown | ajouté |

- **closed / live retiré :** ce cadre a été retiré *après* une mesure où il ratait K
  (0.5B : K = −0.08, t = −0.49 ; 1.5B : K = −0.35, t = −2.28). C'est une décision de
  sélection prise après avoir vu le résultat. Motif invoqué : polysémie de *live*
  (live wire, live broadcast) et de *closed* (closed road, closed shop).
- **resolved / unresolved :** la paire de remplacement a été choisie par Claude, avant
  toute mesure avec elle. C'est une paire morphologique, comme decided / undecided. Elle
  n'avait pas été spécifiée par l'auteur du projet.
- **decided / undecided et known / unknown :** ces deux cadres ont été ajoutés avant la
  mesure ci-dessous.

## Δ moyen par case (nats, moyenne ± écart-type sur 12 domaines)

| cadre | C1 | C2 | C3 | C4 | C5 | C6 |
| --- | --- | --- | --- | --- | --- | --- |
| settled / open | +1.41 ± 0.59 | +1.20 ± 0.50 | +1.33 ± 0.45 | +1.20 ± 0.86 | +0.70 ± 0.61 | +2.02 ± 0.82 |
| right / unproven | +2.17 ± 1.39 | +0.52 ± 1.27 | +2.36 ± 1.02 | +0.60 ± 1.36 | +0.95 ± 1.31 | +0.22 ± 1.24 |
| resolved / unresolved | +3.80 ± 0.67 | +3.61 ± 0.52 | +3.57 ± 0.50 | +3.92 ± 0.68 | +3.38 ± 0.77 | +3.64 ± 0.77 |
| decided / undecided | +4.45 ± 1.10 | +4.14 ± 0.90 | +4.32 ± 0.67 | +4.79 ± 1.04 | +4.67 ± 1.10 | +5.12 ± 1.05 |
| known / unknown | −2.08 ± 0.89 | −2.31 ± 0.50 | −2.50 ± 0.59 | −2.78 ± 0.48 | −2.75 ± 0.75 | −2.90 ± 0.64 |

## K et S, les cinq cadres

| cadre | K | t(K) | S | t(S) | statut |
| --- | --- | --- | --- | --- | --- |
| settled / open | −0.604 | −1.98 | +0.499 | +2.31 | **écarté** : K < 0 |
| right / unproven | +1.945 | +7.42 | −0.432 | −2.77 | calibré |
| resolved / unresolved | +0.164 | +2.14 | +0.231 | +2.36 | calibré (de justesse) |
| decided / undecided | −0.672 | −2.53 | −0.528 | −4.09 | **écarté** : K significativement < 0 |
| known / unknown | +0.824 | +3.94 | +0.439 | +2.86 | calibré |

Les colonnes S des cadres écartés sont affichées pour la transparence. Elles n'entrent
dans aucune lecture.

### Pourquoi deux cadres sont écartés

- **settled / open :** K est négatif (t = −1.98). Le modèle préfère légèrement *open* quand
  tout est clair et vérifiable, c'est-à-dire l'inverse de la calibration attendue.
- **decided / undecided :** K est négatif et significatif (t = −2.53). L'instrument est
  inversé, pas seulement faible. La paire est appariée au mieux, mais ça ne garantit pas
  la calibration. Avec ce cadre, *undecided* devient relativement plus probable quand
  tout est clair (C1) que quand rien n'est disponible (C6).

## Lecture

- **Le seuil du LoRA est atteint :** trois cadres sur cinq passent K à 0.5B. On reste
  donc à 0.5B.
- **Les cadres calibrés ne s'accordent pas sur le signe de S :**
  - right / unproven : S = −0.43 (t = −2.77), penchant vérification publique ;
  - resolved / unresolved : S = +0.23 (t = +2.36), penchant fondement intérieur ;
  - known / unknown : S = +0.44 (t = +2.86), penchant fondement intérieur.
- **Pas de penchant établi :** l'accord entre cadres lexicalement disjoints est la propriété
  qui ferait preuve, et elle n'est pas présente. Deux cadres sur trois donnent S > 0, mais
  un cadre calibré, avec la K la plus forte, donne S < 0 de manière significative. Cette
  mesure n'établit donc pas de penchant de Qwen2.5-0.5B dans un sens ou dans l'autre.
- **resolved / unresolved :** sa calibration est marginale (K = 0.16 nat, t = 2.14), ce qui
  appelle à la prudence sur ce cadre.

## Note sur la mesure précédente (trois cadres)

L'hypothèse « deux cadres sur trois passent K à 0.5B » ne correspond pas à la mesure
précédente. À 0.5B, seul right / unproven passait K. C'est à 1.5B que deux cadres
passaient (settled / open : K = +1.33, t = 3.82 ; right / unproven : K = +2.37, t = 7.36).
Sur la mesure actuelle à 0.5B, settled / open rate toujours K. Le passage de ce cadre à
1.5B pourrait donc refléter un effet de capacité spécifique à ce cadre.

## Suite

Le LoRA attend les 84 démonstrations, qui n'ont pas été fournies et n'ont pas été inventées.
La mesure avant / après se fera sur ces mêmes cinq cadres. La lecture de S restera limitée
aux cadres calibrés, sélectionnés par la règle ci-dessus et déclarés.
