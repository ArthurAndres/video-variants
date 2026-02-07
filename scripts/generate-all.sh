#!/usr/bin/env bash
# ============================================================
# generate-all.sh — Génération en masse de variantes
#
# Usage :
#   ./generate-all.sh <source> <output_dir> <A|B> [--test]
#
# Modèle A : Phase 1+2+4 (sans audio)   → ~360 variantes
# Modèle B : Phase 1+2+3+4 (avec audio) → ~1080 variantes
#
# --test : génère seulement 5 variantes (pour valider)
# ============================================================
set -euo pipefail

SRC="${1:?Usage: $0 <source> <output_dir> <A|B> [--test]}"
OUT_DIR="${2:?Manque le dossier output}"
MODEL="${3:?Modèle requis: A (sans audio) ou B (avec audio)}"
TEST_MODE=false
[ "${4:-}" = "--test" ] && TEST_MODE=true

[ ! -f "$SRC" ] && echo "❌ Source introuvable: $SRC" >&2 && exit 1

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT_DIR"

# --- Configuration ---
SPEEDS=("0.95" "1.00" "1.05" "1.10")
COLORS=("neutral" "warm" "cool" "contrast" "vibrant" "matte" "bw" "teal_orange" "sunset" "clean" "pastel" "noir" "bleach" "cross_process" "hdr")
HOOKS=("none" "zoom" "crop")  # text omis car nécessite texte spécifique
FRAMES=("none" "mirror" "crop")

# Phase 3 — seulement pour Modèle B
PITCHES=("1.03" "1.05" "0.97")

# --- Compteurs ---
TOTAL=0
SUCCESS=0
FAIL=0
START_TIME=$(date +%s)

# --- Calcul du nombre total ---
case "$MODEL" in
  A)
    EXPECTED=$(( ${#SPEEDS[@]} * ${#COLORS[@]} * ${#HOOKS[@]} * ${#FRAMES[@]} ))
    echo "📦 Modèle A (sans audio) — $EXPECTED variantes attendues"
    ;;
  B)
    EXPECTED=$(( ${#SPEEDS[@]} * ${#COLORS[@]} * ${#HOOKS[@]} * ${#PITCHES[@]} * ${#FRAMES[@]} ))
    echo "📦 Modèle B (avec audio) — $EXPECTED variantes attendues"
    ;;
  *)
    echo "❌ Modèle inconnu: $MODEL (A ou B)" >&2 && exit 2 ;;
esac

if $TEST_MODE; then
  echo "🧪 Mode test : 5 variantes max"
fi

echo "Source : $SRC"
echo "Output : $OUT_DIR"
echo "Début  : $(date '+%Y-%m-%d %H:%M:%S')"
echo "---"

# --- Boucle de génération ---
for speed in "${SPEEDS[@]}"; do
  for color in "${COLORS[@]}"; do
    for hook in "${HOOKS[@]}"; do

      if [ "$MODEL" = "A" ]; then
        # Modèle A : pas de phase 3
        for frame in "${FRAMES[@]}"; do
          TOTAL=$((TOTAL+1))
          if $TEST_MODE && [ $TOTAL -gt 5 ]; then break 4; fi

          FILENAME="v${TOTAL}_${speed}_${color}_${hook}_${frame}.mp4"
          echo -n "[${TOTAL}/${EXPECTED}] ${FILENAME}..."

          if "${SCRIPT_DIR}/render-variant.sh" "$SRC" "${OUT_DIR}/${FILENAME}" \
            --speed "$speed" --color "$color" --hook "$hook" --frame "$frame" \
            > /dev/null 2>&1; then
            echo " ✅"
            SUCCESS=$((SUCCESS+1))
          else
            echo " ❌"
            FAIL=$((FAIL+1))
          fi
        done

      else
        # Modèle B : avec phase 3 (pitch)
        for pitch in "${PITCHES[@]}"; do
          for frame in "${FRAMES[@]}"; do
            TOTAL=$((TOTAL+1))
            if $TEST_MODE && [ $TOTAL -gt 5 ]; then break 5; fi

            FILENAME="v${TOTAL}_${speed}_${color}_${hook}_p${pitch}_${frame}.mp4"
            echo -n "[${TOTAL}/${EXPECTED}] ${FILENAME}..."

            if "${SCRIPT_DIR}/render-variant.sh" "$SRC" "${OUT_DIR}/${FILENAME}" \
              --speed "$speed" --color "$color" --hook "$hook" \
              --voice pitch --voice-pitch "$pitch" --frame "$frame" \
              > /dev/null 2>&1; then
              echo " ✅"
              SUCCESS=$((SUCCESS+1))
            else
              echo " ❌"
              FAIL=$((FAIL+1))
            fi
          done
        done
      fi

    done
  done
done

# --- Résumé ---
END_TIME=$(date +%s)
ELAPSED=$(( END_TIME - START_TIME ))
MINUTES=$(( ELAPSED / 60 ))
SECONDS=$(( ELAPSED % 60 ))
TOTAL_SIZE=$(du -sh "$OUT_DIR" 2>/dev/null | cut -f1)

echo ""
echo "========================================"
echo " Génération terminée"
echo "========================================"
echo " Modèle  : $MODEL"
echo " Total   : $TOTAL"
echo " ✅ OK   : $SUCCESS"
echo " ❌ Fail : $FAIL"
echo " Durée   : ${MINUTES}m ${SECONDS}s"
echo " Taille  : $TOTAL_SIZE"
echo " Output  : $OUT_DIR"
echo "========================================"
