#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[$(date)] Démarrage du réentraînement..."
docker compose exec -T api python train.py
echo "[$(date)] Réentraînement terminé."
