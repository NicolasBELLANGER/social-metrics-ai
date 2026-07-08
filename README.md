# API d'Analyse de Sentiments — SocialMetrics AI

Service Flask d'analyse de sentiment pour tweets, développé pour le client **Daunale Treupe**.

Chaque tweet reçoit un score entre **-1** (très négatif) et **1** (très positif), calculé à partir de deux modèles de régression logistique (positif / négatif).

---

## Prérequis

- [Docker](https://www.docker.com/) et Docker Compose
- (Optionnel) `curl` pour tester l'API

> **Note macOS** : le port 5000 est souvent occupé par AirPlay Receiver. L'API est exposée sur le port **5001**.

---

## Installation et lancement

### 1. Cloner le projet

```bash
git clone https://github.com/NicolasBELLANGER/social-metrics-ai
cd social-metrics-ai