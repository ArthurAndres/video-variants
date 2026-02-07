#!/usr/bin/env bash
# ============================================================
# render-color-speed.sh — Phase 1 : Colorimétrie + Vitesse
#
# Usage : ./render-color-speed.sh <source> <output> <speed> <color>
#
# Speeds  : 0.95 | 1.00 | 1.05 | 1.10
# Colors  : neutral | warm | cool | contrast | vibrant | matte
#           bw | teal_orange | sunset | clean | pastel | noir
#           bleach | cross_process | hdr
# ============================================================
set -euo pipefail

SRC="${1:?Usage: $0 <source> <output> <speed> <color_preset>}"
OUT="${2:?Manque le chemin output}"
SPEED="${3:-1.0}"
PRESET="${4:-neutral}"

[ ! -f "$SRC" ] && echo "❌ Source introuvable: $SRC" >&2 && exit 1

# --- Presets couleur → filtres FFmpeg ---
case "$PRESET" in
  neutral)       VF="eq=contrast=1.0:saturation=1.0:brightness=0.0" ;;
  warm)          VF="eq=saturation=1.10:brightness=0.02,colorbalance=rs=0.06:gs=-0.02:bs=-0.06" ;;
  cool)          VF="eq=saturation=1.05,colorbalance=rs=-0.06:gs=0.00:bs=0.06" ;;
  contrast)      VF="eq=contrast=1.15:saturation=1.05" ;;
  vibrant)       VF="eq=contrast=1.10:saturation=1.25" ;;
  matte)         VF="curves=preset=lighter,eq=contrast=0.95:saturation=0.90" ;;
  bw)            VF="format=gray" ;;
  teal_orange)   VF="colorbalance=rs=0.08:gs=-0.03:bs=-0.08:mh=-0.05:ms=0.02:ml=0.05,eq=saturation=1.15:contrast=1.05" ;;
  sunset)        VF="colorbalance=rs=0.10:gs=0.03:bs=-0.08,eq=saturation=1.15:brightness=0.03:contrast=1.05" ;;
  clean)         VF="eq=brightness=0.05:contrast=1.05:saturation=1.05,unsharp=3:3:0.5" ;;
  pastel)        VF="eq=saturation=0.75:brightness=0.06:contrast=0.92" ;;
  noir)          VF="eq=contrast=1.30:brightness=-0.05:saturation=0.85,curves=preset=darker" ;;
  bleach)        VF="eq=contrast=1.20:saturation=0.60:brightness=0.03" ;;
  cross_process) VF="colorbalance=rs=0.05:gs=-0.05:bs=0.10:mh=0.05:ms=-0.03:ml=-0.05,eq=saturation=1.20:contrast=1.10" ;;
  hdr)           VF="eq=contrast=1.20:saturation=1.20:brightness=0.02,unsharp=5:5:0.8" ;;
  *)
    echo "❌ Preset inconnu: $PRESET" >&2
    echo "Dispo: neutral warm cool contrast vibrant matte bw teal_orange sunset clean pastel noir bleach cross_process hdr" >&2
    exit 2 ;;
esac

# --- Filtres vitesse ---
VIDEO_FILTER="${VF},setpts=PTS/${SPEED}"
AUDIO_FILTER="atempo=${SPEED}"

# --- Rendu ---
ffmpeg -y -hide_banner -loglevel error \
  -i "$SRC" \
  -vf "${VIDEO_FILTER}" \
  -af "${AUDIO_FILTER}" \
  -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  "$OUT"

[ -f "$OUT" ] && [ -s "$OUT" ] && echo "✅ Phase1 OK: $OUT ($(du -h "$OUT" | cut -f1)) [speed=${SPEED}, color=${PRESET}]" && exit 0
echo "❌ Échec rendu" >&2 && exit 1
