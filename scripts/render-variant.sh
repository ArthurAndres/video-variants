#!/usr/bin/env bash
# ============================================================
# render-variant.sh — Pipeline combiné (toutes phases)
#
# Applique les 4 phases en séquence sur une vidéo source.
# Chaque phase produit un fichier intermédiaire qui est passé
# à la phase suivante. Les fichiers intermédiaires sont nettoyés.
#
# Usage :
#   ./render-variant.sh <source> <o> [options]
#
# Options :
#   --speed <0.95|1.00|1.05|1.10>       Phase 1 (défaut: 1.0)
#   --color <preset>                     Phase 1 (défaut: neutral)
#   --hook <none|text|zoom|crop>         Phase 2 (défaut: none)
#   --hook-text "texte"                  Phase 2 texte du hook
#   --voice <none|tts|pitch>             Phase 3 (défaut: none)
#   --voice-id <edge_tts_voice>          Phase 3 ID voix
#   --voice-script <fichier.txt>         Phase 3 fichier texte
#   --voice-pitch <factor>               Phase 3 facteur pitch
#   --frame <none|mirror|crop|both>      Phase 4 (défaut: none)
#   --tmp <dir>                          Dossier temp (défaut: /tmp)
#
# Exemples :
#   # Modèle A minimal
#   ./render-variant.sh in.mp4 out.mp4 --speed 1.05 --color warm
#
#   # Modèle A complet
#   ./render-variant.sh in.mp4 out.mp4 --speed 1.05 --color warm \
#     --hook zoom --frame mirror
#
#   # Modèle B complet
#   ./render-variant.sh in.mp4 out.mp4 --speed 1.05 --color warm \
#     --hook text --hook-text "WOW" --voice tts \
#     --voice-id fr-FR-HenriNeural --voice-script script.txt \
#     --frame crop
# ============================================================
set -euo pipefail

# --- Parse args ---
SRC="${1:?Usage: $0 <source> <o> [options]}"
OUT="${2:?Manque le chemin output}"
shift 2

SPEED="1.0"
COLOR="neutral"
HOOK="none"
HOOK_TEXT=""
VOICE="none"
VOICE_ID="fr-FR-HenriNeural"
VOICE_SCRIPT=""
VOICE_PITCH="1.05"
FRAME="none"
TMP_BASE="/tmp"

while [ $# -gt 0 ]; do
  case "$1" in
    --speed)        SPEED="$2"; shift 2 ;;
    --color)        COLOR="$2"; shift 2 ;;
    --hook)         HOOK="$2"; shift 2 ;;
    --hook-text)    HOOK_TEXT="$2"; shift 2 ;;
    --voice)        VOICE="$2"; shift 2 ;;
    --voice-id)     VOICE_ID="$2"; shift 2 ;;
    --voice-script) VOICE_SCRIPT="$2"; shift 2 ;;
    --voice-pitch)  VOICE_PITCH="$2"; shift 2 ;;
    --frame)        FRAME="$2"; shift 2 ;;
    --tmp)          TMP_BASE="$2"; shift 2 ;;
    *)              echo "Option inconnue: $1" >&2; exit 2 ;;
  esac
done

[ ! -f "$SRC" ] && echo "❌ Source introuvable: $SRC" >&2 && exit 1

# --- Dossier temp ---
TMP_DIR=$(mktemp -d "${TMP_BASE}/variant-XXXXXX")
trap "rm -rf $TMP_DIR" EXIT

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CURRENT="$SRC"
STEP=0

variant_name="${SPEED}_${COLOR}_${HOOK}_${VOICE}_${FRAME}"
echo "🎬 Variante: ${variant_name}"

# --- Phase 1 : Couleur + Vitesse ---
if [ "$SPEED" != "1.0" ] || [ "$COLOR" != "neutral" ]; then
  STEP=$((STEP+1))
  NEXT="${TMP_DIR}/step${STEP}_color.mp4"
  "${SCRIPT_DIR}/render-color-speed.sh" "$CURRENT" "$NEXT" "$SPEED" "$COLOR"
  CURRENT="$NEXT"
else
  echo "  ⏭️  Phase 1 skip (neutral/1.0)"
fi

# --- Phase 2 : Hook ---
if [ "$HOOK" != "none" ]; then
  STEP=$((STEP+1))
  NEXT="${TMP_DIR}/step${STEP}_hook.mp4"
  if [ "$HOOK" = "text" ]; then
    "${SCRIPT_DIR}/render-hooks.sh" "$CURRENT" "$NEXT" text "$HOOK_TEXT"
  else
    "${SCRIPT_DIR}/render-hooks.sh" "$CURRENT" "$NEXT" "$HOOK"
  fi
  CURRENT="$NEXT"
else
  echo "  ⏭️  Phase 2 skip (no hook)"
fi

# --- Phase 3 : Audio ---
if [ "$VOICE" != "none" ]; then
  STEP=$((STEP+1))
  NEXT="${TMP_DIR}/step${STEP}_voice.mp4"
  case "$VOICE" in
    tts)
      "${SCRIPT_DIR}/render-voice.sh" "$CURRENT" "$NEXT" tts "$VOICE_ID" "$VOICE_SCRIPT"
      ;;
    pitch)
      "${SCRIPT_DIR}/render-voice.sh" "$CURRENT" "$NEXT" pitch "$VOICE_PITCH"
      ;;
  esac
  CURRENT="$NEXT"
else
  echo "  ⏭️  Phase 3 skip (no voice)"
fi

# --- Phase 4 : Cadrage ---
if [ "$FRAME" != "none" ]; then
  STEP=$((STEP+1))
  NEXT="${TMP_DIR}/step${STEP}_frame.mp4"
  "${SCRIPT_DIR}/render-crop-mirror.sh" "$CURRENT" "$NEXT" "$FRAME"
  CURRENT="$NEXT"
else
  echo "  ⏭️  Phase 4 skip (no frame)"
fi

# --- Copie finale ---
cp "$CURRENT" "$OUT"

if [ -f "$OUT" ] && [ -s "$OUT" ]; then
  SIZE=$(du -h "$OUT" | cut -f1)
  echo "✅ Variante OK: $OUT ($SIZE)"
  echo "   speed=${SPEED} color=${COLOR} hook=${HOOK} voice=${VOICE} frame=${FRAME}"
  exit 0
else
  echo "❌ Échec génération variante" >&2
  exit 1
fi
