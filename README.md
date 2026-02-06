# Freelance Market Fetcher

Agregateur d'offres freelance/emploi qui recupere les jobs depuis des APIs legales et permet l'ajout manuel pour les plateformes sans API (LinkedIn, Free-Work, etc.).

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Fonctionnalites

- **Aggregation multi-sources** - Recupere les offres depuis plusieurs APIs legales
- **Ajout manuel** - Formulaire pour ajouter des offres de n'importe quelle plateforme
- **Dashboard unifie** - Toutes les offres en un seul endroit avec filtres
- **Analyse du marche** - Top technologies, salaires moyens, experience requise
- **Suivi des candidatures** - Favoris, statut "postule", notes personnelles
- **Export CSV** - Telechargez vos offres filtrees

## Capture d'ecran

```
+------------------------------------------+
|  JobFetcher    Offres | Analyse | +Ajouter |
+------------------------------------------+
|  [Fetch All Jobs]     Last: 2024-01-15   |
|  +--------------------------------------+ |
|  | Filtres: Source | Type | Recherche  | |
|  +--------------------------------------+ |
|  | Senior Python Dev    | TechCorp     | |
|  | Paris | Remote | 500-700 EUR/j     | |
|  +--------------------------------------+ |
+------------------------------------------+
```

## Sources de donnees (100% legales)

### Sans authentification (pret a l'emploi)
| Source | Description | Rate Limit |
|--------|-------------|------------|
| [RemoteOK](https://remoteok.com) | Jobs remote internationaux | Illimite |
| [Remotive](https://remotive.com) | Jobs remote tech | 4/jour |
| [Arbeitnow](https://arbeitnow.com) | Jobs Europe | Illimite |

### Avec cle API gratuite
| Source | Description | Inscription |
|--------|-------------|-------------|
| [France Travail](https://francetravail.io) | Pole Emploi officiel | OAuth2 gratuit |
| [Careerjet](https://www.careerjet.com/partners/api/) | Agregateur francais | API key gratuite |
| [Adzuna](https://developer.adzuna.com/) | Jobs France/Europe | API key gratuite |

### Ajout manuel
Pour LinkedIn, Free-Work, Malt, et toute autre plateforme sans API.

## Installation

### 1. Cloner le repo

```bash
git clone https://github.com/YOUR_USERNAME/freelance_market_fetcher.git
cd freelance_market_fetcher
```

### 2. Creer l'environnement virtuel

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Installer les dependances

```bash
pip install -r requirements.txt
```

### 4. Configurer l'environnement

```bash
cp .env.example .env
```

Editez `.env` pour ajouter vos cles API (optionnel).

### 5. Lancer l'application

```bash
python run.py
```

Ouvrir http://localhost:5000

## Configuration des APIs

### France Travail (recommande pour la France)

1. Inscrivez-vous sur [francetravail.io](https://francetravail.io)
2. Creez une application pour obtenir vos identifiants OAuth2
3. Ajoutez dans `.env`:
```env
FRANCETRAVAIL_CLIENT_ID=votre_client_id
FRANCETRAVAIL_CLIENT_SECRET=votre_client_secret
```

### Careerjet

1. Inscrivez-vous sur [careerjet.com/partners/api](https://www.careerjet.com/partners/api/)
2. Ajoutez dans `.env`:
```env
CAREERJET_AFFID=votre_affiliate_id
```

### Adzuna

1. Inscrivez-vous sur [developer.adzuna.com](https://developer.adzuna.com/)
2. Ajoutez dans `.env`:
```env
ADZUNA_APP_ID=votre_app_id
ADZUNA_API_KEY=votre_api_key
```

## Utilisation

### Dashboard principal (`/`)
- Cliquez sur **"Fetch All Jobs"** pour recuperer les offres
- Utilisez les **filtres** pour affiner la recherche
- Cliquez sur une offre pour voir les details
- Ajoutez aux **favoris** ou marquez comme **postule**

### Analyse du marche (`/analytics`)
- **Top 20 Technologies** - Graphique des technos les plus demandees
- **Salaires moyens** - Par heure, jour, mois et annee
- **Experience requise** - Repartition junior/confirme/senior
- **Diplomes demandes** - Bac+2 a Bac+8

### Ajout manuel (`/jobs/new`)
Pour les offres LinkedIn, Free-Work, ou toute autre source.

### Export CSV (`/api/export/csv`)
Exportez les offres filtrees au format CSV.

## Architecture

```
freelance_market_fetcher/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration
│   ├── models.py             # Modeles SQLAlchemy
│   ├── routes/
│   │   ├── main.py           # Routes principales
│   │   └── api.py            # API endpoints
│   ├── services/
│   │   ├── base_fetcher.py   # Classe abstraite
│   │   ├── remoteok_fetcher.py
│   │   ├── remotive_fetcher.py
│   │   ├── arbeitnow_fetcher.py
│   │   ├── francetravail_fetcher.py
│   │   ├── careerjet_fetcher.py
│   │   ├── adzuna_fetcher.py
│   │   ├── job_aggregator.py # Orchestrateur
│   │   └── market_analyzer.py # Analyse du marche
│   ├── templates/            # Templates Jinja2
│   └── static/               # CSS, JS
├── .env.example              # Variables d'environnement
├── requirements.txt          # Dependances Python
└── run.py                    # Point d'entree
```

## Ajouter une nouvelle source

Creez un nouveau fetcher dans `app/services/`:

```python
from .base_fetcher import BaseFetcher, JobData

class MonFetcher(BaseFetcher):
    SOURCE_NAME = "masource"

    def fetch_jobs(self, **kwargs):
        # Appeler l'API
        response = requests.get("https://api.example.com/jobs")
        return [self.normalize_job(job) for job in response.json()]

    def normalize_job(self, raw_job):
        return JobData(
            external_id=str(raw_job['id']),
            title=raw_job['title'],
            company=raw_job['company'],
            description=raw_job.get('description'),
            location=raw_job.get('location'),
            url=raw_job.get('url'),
            posted_at=self._parse_date(raw_job.get('date'))
        )
```

Puis ajoutez-le dans `job_aggregator.py`.

## Technologies utilisees

- **Backend**: Python 3.9+, Flask 3.0, SQLAlchemy
- **Frontend**: HTML5, CSS3 (vanilla), JavaScript (vanilla)
- **Database**: SQLite (zero config)
- **Charts**: Chart.js

## Roadmap

- [ ] Alertes email pour nouvelles offres
- [ ] Filtres avances (salaire min, remote only)
- [ ] Mode sombre
- [ ] API REST complete
- [ ] Docker support

## Contribution

Les contributions sont les bienvenues ! N'hesitez pas a ouvrir une issue ou une PR.

## License

MIT License - voir [LICENSE](LICENSE) pour plus de details.

## Auteur

Fait avec Claude Code

---

**Note**: Ce projet utilise uniquement des APIs publiques et legales. Aucun scraping de sites proteges.
