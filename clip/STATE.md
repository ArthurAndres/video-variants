# STATE — clip « You Know My Name »

Prompt de référence : `PROMPT_COMPLET_AUTONOME.md` (fourni par l'auteur en pièce jointe, pas dans le dépôt).
Mode économique (section 20 bis) actif : épisodes 1 (0:00-1:28) / 2 (1:28-2:46) / 3 (2:46-4:01), rendu final 1280×720.

## Où on en est
Étape 1 terminée : (a) environnement + (b) analyse du morceau (section 5.2). **Arrêt demandé par l'auteur ici.**

## Environnement (vérifié le 2026-09-27)
- 4 cœurs, 15 Go de RAM, pas de GPU. Python 3.11, Node 22, ffmpeg 6.1.1.
- Installé : skia-python 144, numpy 2.4, opencv 5.0 (headless), scipy 1.17, scikit-image 0.26, librosa 0.11, ultralytics 8.4, matplotlib (+ apt : ffmpeg, libegl1, libgl1).
- Skia renvoie du **BGRA** (vérifié) : inverser les canaux avant ffmpeg.
- Banc d'essai (gravure plein écran à 1 ligne tous les 3 px + pipe x264 CRF 17, 1 cœur) : 16,8 img/s en 720p, 8,2 img/s en 1080p.
  Estimation brute : 4:01 en 720p = 7 230 images ≈ 7 min sur 1 cœur pour ce niveau de charge ; les vraies scènes seront plus lourdes, x4 cœurs en parallèle.
- **Internet restreint** : seuls pypi, npm, GitHub passent. Wikimedia Commons, Met, Rijksmuseum, Smithsonian, Europeana, NASA et Google sont **bloqués (403)** par la politique réseau de l'environnement.
  -> impossible de récupérer soi-même les références en ligne (Création d'Adam, Discobole, Atlas Farnèse, David, gravure d'ouroboros).

## Fichiers reçus / manquants
Reçus : MP3 complet (2 copies, audio décodé identique, md5 e2f3ae82…), `35_17.bvh`, `david_mask.npy`, `atlas_mask.npy`,
4 images (planche de mains à l'encre, planche de mains vectorielles, gravure d'ouroboros, photo du David en contre-plongée).
**Manquants** : `reference_test_0-50s.mp4` (le .htm fourni est la page de conversation, pas la vidéo), `dessin_auteur.jpg`, `enfant_ref.jpg`,
les photos de l'Atlas Farnèse, du Discobole et des mains de Michel-Ange (les masques .npy sont là, mais sans leurs images source).

## Analyse du morceau — résultats (revalidés, écarts avec le prompt signalés)
- Durée 241,19 s. **Tempo 137,5 BPM en moyenne, variable de ~135,2 à ~139,4 BPM** (jeu sans métronome).
  Le « ~136 BPM » du prompt vient d'une médiane quantifiée à 23 ms. Une grille fixe dériverait jusqu'à 0,49 s : **toujours utiliser `temps_s`** (546 temps).
- Demi / double tempo exclus : attaque moyenne 2,49 sur les temps, 1,10 sur les demi-temps, 0,65 au hasard ; autocorrélation 0,52 au tempo contre 0,43 et 0,35 au demi et au double.
- Premier temps : 0,20 s (coup principal à 0,18 s, précédé d'une petite anticipation à 0,105 s). 137 mesures en 4/4, phase confirmée par les impacts (10 des 12 grands impacts tombent sur le temps 1).
- Coupure finale : chute à **238,30 s (3:58,3)**, silence (-40 dB) à 238,80 s. C'est une coupure nette, pas un fondu (le prompt disait « ~3:57 »).
- Grandes sections : A 0:00 · B 0:02-0:16 · C 0:16-0:41 (creux) · D 0:41-1:00 · E 1:00-1:24 · F 1:24-1:38 · G 1:38-2:00 (creux) · D 2:00-2:19 · E 2:19-2:47 · H 2:47-3:02 · E 3:02-3:28 · I 3:28-3:47 · J 3:47-3:58.
  Répétitions : D revient 2 fois et E revient 3 fois ; le bloc des mesures 8-53 se rejoue à l'identique aux mesures 53-98 (cycle de ~79 s). C'est là que placer le motif récurrent.
- Voix : repérage APPROXIMATIF, non fiable pour caler quoi que ce soit.

## Commandes
- `python3 tools/analyze.py` → `analysis/analysis.json`, `analysis/carte.png`, `analysis/mesures.md` (≈ 1 min 30).
- `python3 tools/bench.py 1280 720` → banc d'essai du rendu.

## Prochain pas exact
1. Obtenir de l'auteur : la vidéo de test, `dessin_auteur.jpg`, `enfant_ref.jpg`, et soit les photos de référence (Atlas, Discobole, mains de Michel-Ange, David),
   soit l'ouverture du réseau (upload.wikimedia.org, commons.wikimedia.org).
2. Étudier la vidéo de test (1 image toutes les 0,5 s, planche-contact) et `research_notes.md` (≈ 10 recherches).
3. Poser la question de la CAVERNE DE PLATON, puis reconstruire 0:00-0:50 (annexe B).
