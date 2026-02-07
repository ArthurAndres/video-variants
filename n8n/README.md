# n8n — Workflows de génération

## Prérequis

- **n8n self-hosted** en mode queue (worker séparé)
- **FFmpeg** installé dans le container n8n (image custom `n8n-with-ffmpeg`)
- **Google Drive** credentials configurées dans n8n
- Scripts de rendu dans `/data/render-worker/` (volume monté)

## Architecture n8n

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  n8n main    │────▶│  n8n worker  │────▶│  Google      │
│  (webhook)   │     │  (FFmpeg)    │     │  Drive       │
│  Port 5678   │     │  concurrency:8│    │  (upload)    │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Workflows disponibles

### workflow-model-a.json — Sans modification audio

Pipeline Phase 1 (couleur + vitesse) avec upload Google Drive.
C'est le workflow de base, déjà testé et validé.

**Flux :**
1. Webhook reçoit `{ driveFileId, title, outputFolderId }`
2. Télécharge la vidéo depuis Google Drive
3. Génère 60 variantes (4 vitesses × 15 couleurs)
4. Upload chaque variante sur Google Drive
5. Nettoie les fichiers temporaires

### workflow-model-b.json — Avec modification audio

Extension du modèle A avec phases 2, 3 et 4. *(À configurer après validation du modèle A)*

## Installation

### 1. Docker Compose

Le fichier `docker-compose.yml` est dans `/root/n8n-prod/` sur le VPS.

Configuration clé :
```yaml
services:
  n8n-main:
    image: n8n-with-ffmpeg:latest  # Image custom avec FFmpeg
    environment:
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      - WEBHOOK_URL=https://n8n.basedjew.com/
    volumes:
      - n8n_data:/home/node/.n8n
      - /opt/render-worker:/data/render-worker  # Scripts de rendu

  n8n-worker:
    image: n8n-with-ffmpeg:latest
    command: worker --concurrency=8
    volumes:
      - n8n_data:/home/node/.n8n
      - /opt/render-worker:/data/render-worker
```

### 2. Image custom n8n

Le Dockerfile pour ajouter FFmpeg à n8n :

```dockerfile
FROM n8nio/n8n:latest
USER root
RUN apk add --no-cache ffmpeg curl jq bash
USER node
```

Build :
```bash
cd /root/n8n-prod
docker build -t n8n-with-ffmpeg:latest .
```

### 3. Import du workflow

1. Ouvrir n8n : https://n8n.basedjew.com/
2. Menu → Import from File
3. Sélectionner `workflow-model-a.json`
4. Configurer les credentials Google Drive (4 nœuds Google Drive)
5. Activer le workflow

### 4. Google Drive credentials

Dans n8n → Settings → Credentials → Google Drive OAuth2 :
- Client ID et Client Secret depuis la Google Cloud Console
- Scopes nécessaires : `https://www.googleapis.com/auth/drive`

### 5. Test

```bash
# Appel webhook pour déclencher la génération
curl -X POST https://n8n.basedjew.com/webhook/video-variants \
  -H "Content-Type: application/json" \
  -d '{
    "driveFileId": "ID_DU_FICHIER_GOOGLE_DRIVE",
    "title": "ma-video-test",
    "outputFolderId": "ID_DU_DOSSIER_OUTPUT"
  }'
```

Réponse attendue : `202 Accepted` avec un jobId.

## Chemins dans le container

| Quoi | Chemin container | Chemin VPS |
|------|-----------------|------------|
| Scripts de rendu | `/data/render-worker/` | `/opt/render-worker/` |
| Fichiers temporaires | `/data/render-worker/tmp/` | `/opt/render-worker/tmp/` |
| render.sh | `/data/render-worker/render.sh` | `/opt/render-worker/render.sh` |

## Monitoring

```bash
# Logs n8n main
docker logs n8n-prod-n8n-main-1 --tail 50 -f

# Logs n8n worker
docker logs n8n-prod-n8n-worker-1 --tail 50 -f

# Espace disque
df -h /

# Fichiers temp (à nettoyer si problème)
ls -la /opt/render-worker/tmp/
```

## Troubleshooting

| Problème | Solution |
|----------|----------|
| Webhook ne répond pas | Vérifier que le workflow est activé dans n8n |
| FFmpeg not found | Vérifier l'image Docker : `docker exec n8n-prod-n8n-worker-1 ffmpeg -version` |
| Disk full | Nettoyer `/opt/render-worker/tmp/` et `docker system prune` |
| Google Drive auth fail | Re-créer les credentials OAuth2 dans n8n |
| Worker crash | `docker restart n8n-prod-n8n-worker-1` |
