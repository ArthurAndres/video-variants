# Guide d'installation complet

## 1. VPS — Configuration initiale

### Specs minimales

- **OS** : Ubuntu 22.04 ou 24.04 LTS
- **CPU** : 4 vCPU minimum (8 recommandé pour génération en masse)
- **RAM** : 8 Go minimum
- **Disque** : 50 Go libre minimum
- **Réseau** : Pas nécessaire pour le rendu (FFmpeg est local)

### Installation

```bash
# Se connecter au VPS
ssh root@IP_DU_VPS

# Cloner le repo
cd /root
git clone <url-du-repo> video-variants
cd video-variants

# Lancer l'install
sudo bash scripts/install.sh
```

L'installation fait :
- Installe FFmpeg, curl, jq, bc, fonts
- Installe Python 3 + edge-tts
- Crée `/opt/render-worker/tmp/`
- Copie les scripts dans `/opt/render-worker/`

### Test rapide

```bash
# Générer une vidéo de test (3 secondes)
ffmpeg -f lavfi -i testsrc=size=720x1280:rate=30 \
  -f lavfi -i sine=frequency=1000 \
  -t 3 -c:v libx264 -pix_fmt yuv420p -c:a aac \
  /tmp/test-source.mp4

# Phase 1 : couleur + vitesse
./scripts/render-color-speed.sh /tmp/test-source.mp4 /tmp/test-warm.mp4 1.05 warm
# → Doit afficher "✅ Phase1 OK"

# Phase 4 : miroir
./scripts/render-crop-mirror.sh /tmp/test-source.mp4 /tmp/test-mirror.mp4 mirror
# → Doit afficher "✅ Phase4 OK"

# Pipeline complet (Modèle A)
./scripts/render-variant.sh /tmp/test-source.mp4 /tmp/test-variant.mp4 \
  --speed 1.05 --color warm --hook zoom --frame mirror
# → Doit afficher "✅ Variante OK"
```

## 2. Docker / n8n — Configuration

### 2.1 Docker Compose

Le fichier Docker Compose est dans `/root/n8n-prod/docker-compose.yml`.

Structure des services :
- `n8n-main` : interface web + webhook handler
- `n8n-worker` : exécute les workflows en arrière-plan
- `postgres` : base de données n8n
- `redis` : file d'attente (Bull)

### 2.2 Image custom n8n

On utilise une image n8n custom qui inclut FFmpeg :

```bash
cd /root/n8n-prod

# Créer le Dockerfile
cat > Dockerfile << 'EOF'
FROM n8nio/n8n:latest
USER root
RUN apk add --no-cache ffmpeg curl jq bash bc
USER node
EOF

# Build
docker build -t n8n-with-ffmpeg:latest .
```

### 2.3 Volume render-worker

Les scripts de rendu sont montés dans le container via un volume :

```yaml
volumes:
  - /opt/render-worker:/data/render-worker
```

Ça veut dire que dans le container n8n, les scripts sont accessibles via `/data/render-worker/render-color-speed.sh` etc.

### 2.4 Lancer les containers

```bash
cd /root/n8n-prod
docker compose up -d
```

Vérifier :
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

Tous les containers doivent être "Up".

### 2.5 Import du workflow

1. Ouvrir https://n8n.basedjew.com/
2. Menu hamburger → Import from File
3. Choisir `n8n/workflow-model-a.json`
4. Sauvegarder
5. Configurer les 4 credentials Google Drive
6. Activer le workflow (toggle en haut)

## 3. Google Drive — Configuration

### 3.1 Créer un projet Google Cloud

1. Aller sur https://console.cloud.google.com/
2. Créer un nouveau projet
3. Activer l'API Google Drive
4. Créer des credentials OAuth2 (type "Application Web")
5. Ajouter l'URL de callback n8n : `https://n8n.basedjew.com/rest/oauth2-credential/callback`

### 3.2 Configurer dans n8n

1. n8n → Settings → Credentials → Add Credential → Google Drive OAuth2
2. Renseigner Client ID et Client Secret
3. Cliquer "Connect" → Autoriser dans Google
4. Nommer la credential

### 3.3 Structure Drive recommandée

```
Mon Drive/
├── Video-Sources/          ← Vidéos originales
├── Video-Variants/         ← Output des variantes
│   ├── 2024-02-07_video1/
│   ├── 2024-02-08_video2/
│   └── ...
```

## 4. Utilisation quotidienne

### Génération manuelle (SSH)

```bash
# 1. Upload la vidéo sur le VPS
scp video.mp4 root@IP_VPS:/opt/render-worker/tmp/

# 2. Générer (mode test d'abord !)
cd /root/video-variants
./scripts/generate-all.sh /opt/render-worker/tmp/video.mp4 /opt/render-worker/tmp/output/ A --test

# 3. Vérifier les outputs
ls -la /opt/render-worker/tmp/output/

# 4. Si OK, lancer la génération complète
./scripts/generate-all.sh /opt/render-worker/tmp/video.mp4 /opt/render-worker/tmp/output/ A
```

### Génération via n8n (webhook)

```bash
curl -X POST https://n8n.basedjew.com/webhook/video-variants \
  -H "Content-Type: application/json" \
  -d '{
    "driveFileId": "1abc...",
    "title": "ma-video",
    "outputFolderId": "1xyz..."
  }'
```

### Monitoring

```bash
# Espace disque (critique !)
df -h /

# Logs n8n
docker logs n8n-prod-n8n-worker-1 --tail 20

# Fichiers temp à nettoyer
du -sh /opt/render-worker/tmp/*
rm -rf /opt/render-worker/tmp/*.mp4
```

## 5. Maintenance

### Nettoyage régulier

```bash
# Fichiers temporaires de rendu
rm -rf /opt/render-worker/tmp/*.mp4

# Docker (images et cache inutilisés)
docker system prune -f

# Logs système
journalctl --vacuum-time=7d
```

### Mise à jour des scripts

```bash
cd /root/video-variants
git pull
cp scripts/render-*.sh /opt/render-worker/
cp scripts/generate-all.sh /opt/render-worker/
chmod +x /opt/render-worker/*.sh
```

### Rebuild de l'image n8n

Si FFmpeg doit être mis à jour :

```bash
cd /root/n8n-prod
docker build --no-cache -t n8n-with-ffmpeg:latest .
docker compose down
docker compose up -d
```
