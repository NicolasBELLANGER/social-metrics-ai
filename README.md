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
```

### 2. Démarrer les services

```bash
docker compose up -d --build
```

Cela lance :
- **db** : MySQL 8 avec la table `tweets` (via `db/init.sql`)
- **api** : API Flask sur le port 5001
- **scheduler** : cron hebdomadaire pour le réentraînement

### 3. Entraîner les modèles (première fois)

```bash
docker compose exec api python train.py
```

Ce script :
1. Importe automatiquement le CSV si la table est vide (`db/seed.py`)
2. Entraîne les deux modèles `LogisticRegression`
3. Sauvegarde les modèles dans `models/`
4. Génère les matrices de confusion et les métriques dans `reports/`

---

## Utilisation de l'API

### Endpoint `POST /analyze`

Analyse une liste de tweets et retourne un score de sentiment pour chacun.

**Requête :**

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '["J'\''adore ce produit !", "Service catastrophique, très déçu."]'
```

**Réponse (200) :**

```json
{
  "J'adore ce produit !": 0.9192,
  "Service catastrophique, très déçu.": -0.8869
}
```

### Tester avec `test.json`

Un fichier d'exemple est fourni à la racine du projet :

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d @test.json
```

Contenu de `test.json` (positif, négatif, neutre) :

```json
[
  "J'adore ce produit !",
  "Service catastrophique, très déçu.",
  "Excellent produit, je recommande !",
  "C'est un désastre total.",
  "Rien de particulier à signaler."
]
```

Réponse formatée :

```bash
curl -s -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d @test.json | python3 -m json.tool
```

### Endpoint `GET /health`

Vérifie que l'API est en ligne :

```bash
curl http://localhost:5001/health
```

### Gestion des erreurs

| Code | Cas |
|------|-----|
| 400 | Corps vide, mauvais format (pas une liste de strings) |
| 503 | Modèles non entraînés (lancer `train.py` d'abord) |

---

## Structure du projet

```
├── app.py                  # API Flask
├── train.py                # Entraînement des modèles
├── config.py               # Configuration MySQL
├── db/
│   ├── init.sql            # Création table tweets
│   ├── connection.py       # Connexion MySQL
│   └── seed.py             # Import CSV → MySQL
├── data/
│   └── tweet-dataset.csv   # Dataset annoté (44 tweets)
├── test.json               # Exemple de requête pour POST /analyze
├── models/                 # Modèles entraînés (.joblib)
├── reports/                # Matrices de confusion + métriques (rapport PDF à rédiger)
├── scripts/
│   ├── retrain.sh          # Script de réentraînement manuel
│   └── crontab             # Planification hebdomadaire
├── docker-compose.yml
└── Dockerfile
```

---

## Réentraînement du modèle

### Automatique (cron Docker)

Le service `scheduler` relance `train.py` **tous les lundis à 3h00** via le cron défini dans `scripts/crontab`.

### Manuel

```bash
./scripts/retrain.sh
```

Ou directement :

```bash
docker compose exec api python train.py
```

### Cron sur la machine hôte (alternative)

```bash
chmod +x scripts/retrain.sh
crontab -e
# Ajouter :
0 3 * * 1 /chemin/vers/projet/scripts/retrain.sh >> /var/log/sentiment-retrain.log 2>&1
```

---

## Base de données

### Vérifier les données

```bash
docker compose exec db mysql -u sentiment-api-user -psentiment-api-pass sentiment-api-db -e "SELECT COUNT(*) FROM tweets;"
```

### Structure de la table `tweets`

| Colonne | Type | Description |
|---------|------|-------------|
| id | INT | Identifiant unique |
| text | TEXT | Contenu du tweet |
| positive | TINYINT(1) | 1 si positif, 0 sinon |
| negative | TINYINT(1) | 1 si négatif, 0 sinon |

---

## Rapport d'évaluation

Après l'entraînement, `train.py` génère dans `reports/` :
- `confusion_positive.png` et `confusion_negative.png`
- `metrics.json` (précision, rappel, F1 par classe)

Le rapport PDF (`reports/rapport_evaluation.pdf`) est à rédiger manuellement en s'appuyant sur ces fichiers.

---

## Arrêter les services

```bash
docker compose down
```

Pour supprimer aussi les données MySQL :

```bash
docker compose down -v
```
