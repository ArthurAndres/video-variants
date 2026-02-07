#!/usr/bin/env bash
# ============================================================
# render-crop-mirror.sh — Phase 4 : Cadrage & Miroir
#
# Micro-transformations qui changent le fingerprint visuel
# sans altérer le contenu perceptible.
#
# Usage :
#   ./render-crop-mirror.sh <source> <o> mirror
#   ./render-crop-mirror.sh <source> <o> crop
#   ./render-crop-mirror.sh <source> <o> both
#   ./render-crop-mirror.sh <source> <o> none
# ============================================================
set -euo pipefail

SRC="${1:?Usage: $0 <source> <o> <mirror|crop|both|none>}"
OUT="${2:?Manque le chemin output}"
MODE="${3:-none}"

[ ! -f "$SRC" ] && echo "❌ Source introuvable: $SRC" >&2 && exit 1

case "$MODE" in

  mirror)
    # Retournement horizontal
    ffmpeg -y -hide_banner -loglevel error \
      -i "$SRC" \
      -vf "hflip" \
      -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
      -c:a copy -movflags +faststart \
      "$OUT"
    ;;

  crop)
    # Crop 3% + léger décalage vers la droite, puis rescale à la résolution originale
    # Imperceptible visuellement mais change complètement le fingerprint pixel
    ffmpeg -y -hide_banner -loglevel error \
      -i "$SRC" \
      -vf "crop=iw*0.97:ih*0.97:iw*0.02:iw*0.01,scale=iw/0.97:ih/0.97" \
      -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
      -c:a copy -movflags +faststart \
      "$OUT"
    ;;

  both)
    # Miroir + crop combinés
    ffmpeg -y -hide_banner -loglevel error \
      -i "$SRC" \
      -vf "hflip,crop=iw*0.97:ih*0.97:iw*0.02:iw*0.01,scale=iw/0.97:ih/0.97" \
      -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
      -c:a copy -movflags +faststart \
      "$OUT"
    ;;

  none)
    cp "$SRC" "$OUT"
    echo "✅ Phase4 skip (none): $OUT"
    exit 0
    ;;

  *)
    echo "❌ Mode inconnu: $MODE (mirror|crop|both|none)" >&2 && exit 2 ;;
esac

[ -f "$OUT" ] && [ -s "$OUT" ] && echo "✅ Phase4 OK: $OUT ($(du -h "$OUT" | cut -f1)) [frame=${MODE}]" && exit 0
echo "❌ Échec cadrage" >&2 && exit 1
