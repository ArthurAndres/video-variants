# STATE — clip « You Know My Name »

Prompt de référence : `PROMPT_COMPLET_AUTONOME.md` (fourni par l'auteur en pièce jointe, pas dans le dépôt).
Mode économique (section 20 bis) actif : épisodes 1 (0:00-1:28) / 2 (1:28-2:46) / 3 (2:46-4:01), rendu final 1280×720.

## Où on en est
- Étapes (a) à (d) faites : environnement, analyse, étude du test, références, **reconstruction 0:00-0:50** (`out/test_0-50s_v2.mp4`, hors git).
- **ARRÊT (étape d)** : en attente du retour de l'auteur sur la reconstruction avant de continuer après 0:50.
- Décisions de l'auteur : pas de `dessin_auteur.jpg` (« tu t'en passes ») ; enfant = Badile ; caverne de Platon remplacée par L'ARRIVÉE DES ANUNNAKI (`proposition_anunnaki.md`, réalisée 34,2-36,9 s).
- Contrôles du rendu v2 : 61 coupes, 97 % à ±1 image d'un temps ou demi-temps (médiane 8 ms ; le test : 28 %), aucune fenêtre statique.

## Pipeline de rendu (reprendre ici)
1. `python3 tools/prep_masks.py` (détourages -> assets/masks) puis `python3 tools/prep_assets.py` (gravures -> assets/eng). Modèle YOLO : models/ (téléchargé auto).
   Épreuve de l'enfant : `python3 tools/proof_child.py` AVANT prep_assets (child_profile en dépend).
2. `python3 -m engine.render 0 50 out/x.mp4` (4 processus, ~17 img/s en 720p ; `--preview` = 640×360).
3. Contrôles : `python3 tools/cuts.py out/x.mp4` ; planches : `python3 tools/sheet_video.py out/x.mp4 out/review/s.jpg t0 t1`.
- Code : `engine/core.py` (horloge musicale, papier, ligne d'or), `engine/common.py` (dessin commun), `engine/engrave.py` (gravure A.3),
  `engine/shots_a.py` (0-19,65 s), `shots_b.py` (19,65-40,8 s), `shots_c.py` (40,8-50 s), `engine/timeline.py` (plans calés sur les numéros de temps).
- Sources des figures : Dürer (Adam, Ève), Masaccio (couple chassé, pied), Sourikov (enfant de dos), Badile (enfant de profil), coureur à la torche
  (pélikè à figures rouges = Prométhée, porteurs), Discobole, David, Atlas, Antinoüs (statue), Parthénon, Création, sceau d'Adda, Shamash, Apkallu.
- Échecs notés (règle des 3) : silhouette pleine de l'enfant (Badile) ; gros plan de la main d'Ève (Dürer regravé) -> remplacé par la main d'Adam (Michel-Ange) qui se tend vers le fruit ;
  YOLO instable sur statues/fresques -> union multi-tailles + GrabCut ; soufflet illisible -> four qui respire.

## Points faibles connus de la v2 (à reprendre selon le retour de l'auteur)
- Chevelure de l'enfant (Badile) encore un peu « casque » ; Adam et Ève de Dürer en figures noires : la branche tenue par Adam fait une masse peu lisible.
- Le noir qui se referme (16,5 s) se lit comme une tache ; le serpent caché (6 s) reste discret ; la forge est sage.
- Pas encore de « texte »/titre, pas encore de motif récurrent calé sur les répétitions (après 0:50).

## Environnement (vérifié le 2026-09-27)
- 4 cœurs, 15 Go de RAM, pas de GPU. Python 3.11, Node 22, ffmpeg 6.1.1.
- Installé : skia-python 144, numpy 2.4, opencv 5.0 (headless), scipy 1.17, scikit-image 0.26, librosa 0.11, ultralytics 8.4, matplotlib (+ apt : ffmpeg, libegl1, libgl1).
- Skia renvoie du **BGRA** (vérifié) : inverser les canaux avant ffmpeg.
- Banc d'essai (gravure plein écran à 1 ligne tous les 3 px + pipe x264 CRF 17, 1 cœur) : 16,8 img/s en 720p, 8,2 img/s en 1080p.
  Estimation brute : 4:01 en 720p = 7 230 images ≈ 7 min sur 1 cœur pour ce niveau de charge ; les vraies scènes seront plus lourdes, x4 cœurs en parallèle.
- Réseau : Wikimedia (upload, commons) et Met ouverts par l'auteur. Wikimedia bride les gros originaux : utiliser les vignettes 1920 (voir `sources.md`).

## Fichiers reçus / manquants
Reçus : MP3 complet (2 copies, audio décodé identique, md5 e2f3ae82…), `35_17.bvh`, `david_mask.npy`, `atlas_mask.npy`,
4 images (planche de mains à l'encre, planche de mains vectorielles, gravure d'ouroboros, photo du David en contre-plongée).
Vidéo de test reçue ensuite (`references/reference_test_0-50s.mp4`, audio calé à 0 ms sur le MP3).
Rangés dans `references/` (hors git) : ouroboros_gravure.jpg (592×612), david_contreplongee.jpg (480×640, basse déf.), mains_planche_*.jpg, 35_17.bvh, *_mask.npy.
Références en ligne récupérées (`references/web/hd/`, détail dans `sources.md`) : mains de la Création, Discobole (x2), Atlas Farnèse (x2), David en contre-plongée, ouroboros de Jennis.
Les masques `*_mask.npy` de l'auteur sont grossiers (David de profil avec artefacts, Atlas informe) : détourages à refaire sur les nouvelles photos.
**Manquant** : `dessin_auteur.jpg` (l'enfant est remplacé par une référence libre, voir plus haut).

## Analyse du morceau — résultats (revalidés, écarts avec le prompt signalés)
- Durée 241,19 s. **Tempo 137,5 BPM en moyenne, variable de ~135,2 à ~139,4 BPM** (jeu sans métronome).
  Le « ~136 BPM » du prompt vient d'une médiane quantifiée à 23 ms. Une grille fixe dériverait jusqu'à 0,49 s : **toujours utiliser `temps_s`** (546 temps).
- Demi / double tempo exclus : attaque moyenne 2,49 sur les temps, 1,10 sur les demi-temps, 0,65 au hasard ; autocorrélation 0,52 au tempo contre 0,43 et 0,35 au demi et au double.
- Premier temps : 0,20 s (coup principal à 0,18 s, précédé d'une petite anticipation à 0,105 s). 137 mesures en 4/4, phase confirmée par les impacts (10 des 12 grands impacts tombent sur le temps 1).
- Coupure finale : chute à **238,30 s (3:58,3)**, silence (-40 dB) à 238,80 s. C'est une coupure nette, pas un fondu (le prompt disait « ~3:57 »).
- Grandes sections : A 0:00 · B 0:02-0:16 · C 0:16-0:41 (creux) · D 0:41-1:00 · E 1:00-1:24 · F 1:24-1:38 · G 1:38-2:00 (creux) · D 2:00-2:19 · E 2:19-2:47 · H 2:47-3:02 · E 3:02-3:28 · I 3:28-3:47 · J 3:47-3:58.
  Répétitions : D revient 2 fois et E revient 3 fois ; le bloc des mesures 8-53 se rejoue à l'identique aux mesures 53-98 (cycle de ~79 s). C'est là que placer le motif récurrent.
- Voix : repérage APPROXIMATIF, non fiable pour caler quoi que ce soit.

## Règle de synchro (issue de l'étude du test)
Le son commence 17 ms avant chaque temps de `temps_s` (qui marque le pic d'attaque). Chaque coupe tombe sur l'image `round((temps − 0,017) × 30)`.
Le test n'avait que 28 % de coupes à ±1 image (retard moyen +32 ms) ; objectif ≥ 90 %, vérifié par `tools/cuts.py`.

## Commandes
- `python3 tools/analyze.py` → `analysis/analysis.json`, `analysis/carte.png`, `analysis/mesures.md` (≈ 1 min 30).
- `python3 tools/bench.py 1280 720` → banc d'essai du rendu.
- `python3 tools/contact.py sortie.jpg t0 t1` → planche-contact de la vidéo de test (images extraites dans `references/test_frames/`, 2 img/s).
- `python3 tools/commons.py "requête"` / `python3 tools/fetch_commons.py 1920 prefixe:"File:…"` → recherche et téléchargement sur Commons.
- `python3 tools/cuts.py video.mp4` → coupes détectées, écarts aux temps, fenêtres statiques.

## Prochain pas exact (après validation de 0:00-0:50)
1. Validation de l'auteur : l'enfant d'après Badile ; les 3 plans des Anunnaki.
2. `dessin_auteur.jpg` pour son profil et la statue du dessin (sinon : profil de marbre antique libre de droits pour la statue ; les plans du profil de l'auteur restent en attente).
3. Reconstruire 0:00-0:50 (annexe B + corrections de `etude_video_test.md`), en commençant par le moteur commun et 0-20 s (qui dépend seulement de l'enfant et du profil de l'auteur), puis montrer le résultat et S'ARRÊTER.
