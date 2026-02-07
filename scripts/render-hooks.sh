#!/usr/bin/env bash
# ============================================================
# render-hooks.sh — Phase 2 : Hooks visuels
#
# Modifie les 2-3 premières secondes pour changer le "hook"
# (les premières frames sont le signal le plus fort sur TikTok)
#
# Usage :
#   ./render-hooks.sh <source> <o> text "Mon texte"
#   ./render-hooks.sh <source> <o> zoom
#   ./render-hooks.sh <source> <o> crop
#   ./render-hooks.sh <source> <o> none
# ============================================================
set -euo pipefail

SRC="${1:?Usage: $0 <source> <o> <text|zoom|crop|none> [texte]}"
OUT="${2:?Manque le chemin output}"
HOOK="${3:-none}"
TEXT="${4:-}"
DURATION=2.5  # secondes du hook

[ ! -f "$SRC" ] && echo "❌ Source introuvable: $SRC" >&2 && exit 1

case "$HOOK" in

  text)
    [ -z "$TEXT" ] && echo "❌ Hook 'text' nécessite un texte en arg 4" >&2 && exit 2
    # Escape les caractères spéciaux pour drawtext
    SAFE_TEXT=$(echo "$TEXT" | sed "s/'/\\\\'/g" | sed 's/:/\\:/g')
    ffmpeg -y -hide_banner -loglevel error \
      -i "$SRC" \
      -vf "drawtext=text='${SAFE_TEXT}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=44:fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h*0.12:enable='between(t,0,${DURATION})'" \
      -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
      -c:a copy \
      -movflags +faststart \
      "$OUT"
    ;;

  zoom)
    # Zoom 1.0 → 1.15 sur les premières secondes, puis normal
    # On utilise zoompan sur un split/concat
    ffmpeg -y -hide_banner -loglevel error \
      -i "$SRC" \
      -filter_complex "\
        [0:v]split=2[a][b]; \
        [a]trim=0:${DURATION},setpts=PTS-STARTPTS,scale=iw*1.15:ih*1.15,crop=iw/1.15:ih/1.15:(iw-iw/1.15)/2:(ih-ih/1.15)/2[intro]; \
        [b]trim=${DURATION},setpts=PTS-STARTPTS[rest]; \
        [intro][rest]concat=n=2:v=1:a=0[vout]" \
      -map "[vout]" -map 0:a? \
      -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
      -c:a copy \
      -movflags +faststart \
      "$OUT"
    ;;

  crop)
    # Recadrage décalé (5% à gauche) sur l'intro, puis retour normal
    ffmpeg -y -hide_banner -loglevel error \
      -i "$SRC" \
      -filter_complex "\
        [0:v]split=2[a][b]; \
        [a]trim=0:${DURATION},setpts=PTS-STARTPTS,crop=iw*0.92:ih:iw*0.06:0,scale=iw/0.92:ih[intro]; \
        [b]trim=${DURATION},setpts=PTS-STARTPTS[rest]; \
        [intro][rest]concat=n=2:v=1:a=0[vout]" \
      -map "[vout]" -map 0:a? \
      -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
      -c:a copy \
      -movflags +faststart \
      "$OUT"
    ;;

  none)
    cp "$SRC" "$OUT"
    echo "✅ Phase2 skip (none): $OUT"
    exit 0
    ;;

  *)
    echo "❌ Hook inconnu: $HOOK (text|zoom|crop|none)" >&2 && exit 2 ;;
esac

[ -f "$OUT" ] && [ -s "$OUT" ] && echo "✅ Phase2 OK: $OUT ($(du -h "$OUT" | cut -f1)) [hook=${HOOK}]" && exit 0
echo "❌ Échec hook" >&2 && exit 1
