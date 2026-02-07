#!/usr/bin/env bash
# ============================================================
# render-voice.sh — Phase 3 : Modification audio / Voix IA
#
# Modes :
#   tts   → Remplace l'audio par une voix Edge TTS
#   pitch → Change la tonalité de l'audio existant
#   none  → Pas de modification
#
# Usage :
#   ./render-voice.sh <source> <o> tts <voice_id> <text_file>
#   ./render-voice.sh <source> <o> pitch <factor>
#   ./render-voice.sh <source> <o> none
#
# Voix Edge TTS françaises :
#   fr-FR-HenriNeural   (homme)
#   fr-FR-DeniseNeural   (femme)
#   fr-FR-AlainNeural    (homme 2)
#   fr-FR-EloiseNeural   (femme 2)
#
# Pré-requis : pip install edge-tts
# ============================================================
set -euo pipefail

SRC="${1:?Usage: $0 <source> <o> <tts|pitch|none> [args...]}"
OUT="${2:?Manque le chemin output}"
MODE="${3:-none}"

[ ! -f "$SRC" ] && echo "❌ Source introuvable: $SRC" >&2 && exit 1

TMP_DIR=$(mktemp -d /tmp/voice-XXXXXX)
trap "rm -rf $TMP_DIR" EXIT

case "$MODE" in

  tts)
    VOICE="${4:?Mode tts : $0 src out tts <voice_id> <text_file>}"
    TEXT_FILE="${5:?Mode tts : $0 src out tts voice_id <text_file>}"
    [ ! -f "$TEXT_FILE" ] && echo "❌ Fichier texte introuvable: $TEXT_FILE" >&2 && exit 2

    if ! command -v edge-tts &>/dev/null; then
      echo "❌ edge-tts non installé → pip install edge-tts" >&2
      exit 3
    fi

    echo "🎙️  Génération TTS [${VOICE}]..."
    edge-tts --voice "$VOICE" --text "$(cat "$TEXT_FILE")" --write-media "$TMP_DIR/tts.mp3"

    # Convertir en WAV
    ffmpeg -y -hide_banner -loglevel error \
      -i "$TMP_DIR/tts.mp3" -ar 44100 -ac 2 "$TMP_DIR/tts.wav"

    # Remplacer audio (durée = plus courte entre vidéo et audio)
    ffmpeg -y -hide_banner -loglevel error \
      -i "$SRC" -i "$TMP_DIR/tts.wav" \
      -map 0:v:0 -map 1:a:0 \
      -c:v copy -c:a aac -b:a 128k \
      -shortest -movflags +faststart \
      "$OUT"

    echo "✅ Phase3 OK: $OUT [voice=${VOICE}]"
    ;;

  pitch)
    FACTOR="${4:-1.05}"
    SR=44100
    NEW_SR=$(echo "$SR * $FACTOR" | bc | cut -d. -f1)

    ffmpeg -y -hide_banner -loglevel error \
      -i "$SRC" \
      -af "asetrate=${NEW_SR},aresample=${SR}" \
      -c:v copy -c:a aac -b:a 128k \
      -movflags +faststart \
      "$OUT"

    echo "✅ Phase3 OK: $OUT [pitch=${FACTOR}]"
    ;;

  none)
    cp "$SRC" "$OUT"
    echo "✅ Phase3 skip (none): $OUT"
    ;;

  *)
    echo "❌ Mode inconnu: $MODE (tts|pitch|none)" >&2 && exit 2 ;;
esac

exit 0
