# 🎬 Video Variants Generator

Génération automatisée de variantes uniques à partir d'une seule vidéo source.
Conçu pour TikTok, Instagram Reels et YouTube Shorts.

---

## Concept

Une vidéo → des centaines de variantes **indétectables** par les algos de contenu dupliqué.

Le système combine **4 axes de transformation** indépendants. Chaque axe modifie un aspect différent de la vidéo, et les combinaisons multiplient les variantes de façon exponentielle.

## Les 2 modèles

| Modèle | Phases utilisées | Variantes | Détection | Audio |
|--------|-----------------|-----------|-----------|-------|
| **A — Sans audio** | Phase 1 + 2 + 4 | ~360 | ~85% safe | Audio original conservé |
| **B — Avec audio** | Phase 1 + 2 + 3 + 4 | ~1080 | ~98% safe | Voix IA ou pitch shift |

Le modèle A suffit pour la majorité des cas. Le modèle B est recommandé si l'audio est le signal principal de détection (cas fréquent sur Meta et YouTube Shorts).

---

## Les 4 phases de transformation

### Phase 1 — Colorimétrie + Vitesse
**Script :** `scripts/render-color-speed.sh`

Change la colorimétrie et la vitesse de la vidéo. C'est la base de tout le système.

- **4 vitesses** : 0.95×, 1.00×, 1.05×, 1.10×
- **15 presets couleur** : neutral, warm, cool, contrast, vibrant, matte, bw, teal_orange, sunset, clean, pastel, noir, bleach, cross_process, hdr

→ **60 combinaisons** (4 × 15)

```bash
./scripts/render-color-speed.sh input.mp4 output.mp4 1.05 warm
```

### Phase 2 — Hooks visuels
**Script :** `scripts/render-hooks.sh`

Modifie les 2-3 premières secondes (intro) de la vidéo. C'est le levier le plus puissant sur TikTok : l'algorithme pèse fortement les premières frames pour identifier les duplicatas.

- **text** : texte accrocheur superposé au début
- **zoom** : zoom progressif sur l'intro
- **crop** : recadrage différent sur l'intro

→ **×3 multiplicateur** (+ la version sans hook)

```bash
./scripts/render-hooks.sh input.mp4 output.mp4 text "Personne ne sait ça 👀"
./scripts/render-hooks.sh input.mp4 output.mp4 zoom
./scripts/render-hooks.sh input.mp4 output.mp4 crop
```

### Phase 3 — Audio / Voix IA *(Modèle B uniquement)*
**Script :** `scripts/render-voice.sh`

Remplace ou modifie la piste audio. L'audio fingerprint est le signal #1 de détection sur Meta et YouTube.

- **tts** : voix IA via Edge TTS (gratuit, Microsoft)
- **pitch** : change la tonalité de l'audio existant
- **none** : conserve l'audio original

Voix françaises disponibles (Edge TTS) :

| ID | Genre |
|----|-------|
| `fr-FR-HenriNeural` | Homme |
| `fr-FR-DeniseNeural` | Femme |
| `fr-FR-AlainNeural` | Homme 2 |
| `fr-FR-EloiseNeural` | Femme 2 |

```bash
# Remplacement par voix IA
./scripts/render-voice.sh input.mp4 output.mp4 tts fr-FR-HenriNeural script.txt

# Pitch shift simple
./scripts/render-voice.sh input.mp4 output.mp4 pitch 1.05
```

### Phase 4 — Cadrage & Miroir
**Script :** `scripts/render-crop-mirror.sh`

Micro-transformations visuelles qui changent le fingerprint sans altérer le contenu perceptible.

- **mirror** : retournement horizontal
- **crop** : recadrage de 2-5% + repositionnement
- **both** : miroir + crop combinés

→ **×2 multiplicateur**

```bash
./scripts/render-crop-mirror.sh input.mp4 output.mp4 mirror
./scripts/render-crop-mirror.sh input.mp4 output.mp4 crop
```

---

## Utilisation

### Script principal

Le script `render-variant.sh` combine toutes les phases en un seul appel :

```bash
# Phase 1 seule
./scripts/render-variant.sh input.mp4 output.mp4 \
  --speed 1.05 --color warm

# Phase 1 + 2 + 4 (Modèle A)
./scripts/render-variant.sh input.mp4 output.mp4 \
  --speed 1.05 --color warm --hook zoom --frame mirror

# Toutes les phases (Modèle B)
./scripts/render-variant.sh input.mp4 output.mp4 \
  --speed 1.05 --color warm --hook text --hook-text "WOW 🔥" \
  --voice tts --voice-id fr-FR-HenriNeural --voice-script script.txt \
  --frame crop
```

### Génération en masse

Le script `generate-all.sh` génère toutes les combinaisons :

```bash
# Modèle A — sans audio (360 variantes)
./scripts/generate-all.sh input.mp4 ./output/ A

# Modèle B — avec audio (1080 variantes)
./scripts/generate-all.sh input.mp4 ./output/ B

# Test rapide — 5 variantes seulement
./scripts/generate-all.sh input.mp4 ./output/ A --test
```

### Via n8n (automatisé)

Le workflow n8n orchestre tout automatiquement :

1. Reçoit un fichier vidéo via webhook
2. Génère toutes les variantes
3. Upload les résultats sur Google Drive

Voir `n8n/README.md` pour le setup.

---

## Installation

### Pré-requis

| Composant | Version | Obligatoire |
|-----------|---------|-------------|
| Ubuntu | 22.04 / 24.04 | ✅ |
| FFmpeg | 6.x+ | ✅ |
| Python 3 | 3.10+ | Modèle B uniquement |
| edge-tts | latest | Modèle B uniquement |
| n8n | self-hosted | Pour automatisation |

### Installation rapide

```bash
git clone <url-du-repo> && cd video-variants
sudo bash scripts/install.sh

# Test
./scripts/render-color-speed.sh test.mp4 out.mp4 1.05 warm
```

### Installation détaillée

Voir `docs/SETUP.md`

---

## Structure du repo

```
video-variants/
├── README.md                       ← Ce fichier
├── scripts/
│   ├── install.sh                  ← Setup VPS
│   ├── render-color-speed.sh       ← Phase 1
│   ├── render-hooks.sh             ← Phase 2
│   ├── render-voice.sh             ← Phase 3
│   ├── render-crop-mirror.sh       ← Phase 4
│   ├── render-variant.sh           ← Combiné (1 vidéo)
│   └── generate-all.sh            ← Génération en masse
├── n8n/
│   ├── README.md                   ← Guide n8n
│   ├── workflow-model-a.json       ← Workflow sans audio
│   └── workflow-model-b.json       ← Workflow avec audio
├── config/
│   ├── presets.json                ← Presets couleur/vitesse
│   └── hooks.json                  ← Textes des hooks
└── docs/
    └── SETUP.md                    ← Guide d'installation
```

---

## Licence

Usage interne uniquement. Ne pas redistribuer.
