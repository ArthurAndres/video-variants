#!/usr/bin/env bash
# ============================================================
# install.sh — Installation des dépendances VPS
# Usage : sudo bash scripts/install.sh
# ============================================================
set -euo pipefail

echo "========================================"
echo " Video Variants — Installation"
echo "========================================"
echo ""

# --- FFmpeg ---
echo "[1/5] FFmpeg..."
if command -v ffmpeg &>/dev/null; then
  echo "  ✅ FFmpeg déjà installé ($(ffmpeg -version 2>&1 | head -1 | awk '{print $3}'))"
else
  apt update -qq && apt install -y ffmpeg
  echo "  ✅ FFmpeg installé"
fi

# --- Outils système ---
echo "[2/5] Outils (curl, jq, bc)..."
apt install -y curl jq bc fonts-dejavu-core 2>/dev/null
echo "  ✅ OK"

# --- Python + Edge TTS ---
echo "[3/5] Python + Edge TTS (pour Modèle B)..."
if command -v python3 &>/dev/null; then
  echo "  ✅ Python3 déjà installé"
else
  apt install -y python3 python3-pip
fi
pip install edge-tts --break-system-packages 2>/dev/null || pip install edge-tts 2>/dev/null || echo "  ⚠️  Edge TTS : install manuelle requise (pip install edge-tts)"
echo "  ✅ Edge TTS installé"

# --- Dossier de travail ---
echo "[4/5] Dossier de travail..."
mkdir -p /opt/render-worker/tmp
chmod 755 /opt/render-worker /opt/render-worker/tmp
echo "  ✅ /opt/render-worker/tmp"

# --- Scripts ---
echo "[5/5] Copie des scripts..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR"/render-*.sh /opt/render-worker/ 2>/dev/null || true
cp "$SCRIPT_DIR"/generate-all.sh /opt/render-worker/ 2>/dev/null || true
chmod +x /opt/render-worker/*.sh 2>/dev/null || true
echo "  ✅ Scripts dans /opt/render-worker/"

echo ""
echo "========================================"
echo " Installation terminée ✅"
echo "========================================"
echo ""
echo "Test rapide :"
echo "  ffmpeg -version | head -1"
echo "  edge-tts --list-voices | grep fr-FR"
echo ""
echo "Générer une vidéo test :"
echo "  ffmpeg -f lavfi -i testsrc=size=720x1280:rate=30 -f lavfi -i sine=frequency=1000 -t 3 -c:v libx264 -pix_fmt yuv420p -c:a aac /tmp/test.mp4"
echo "  ./scripts/render-color-speed.sh /tmp/test.mp4 /tmp/out.mp4 1.05 warm"
