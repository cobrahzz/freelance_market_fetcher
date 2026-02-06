import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .base_fetcher import BaseFetcher, JobData


class FranceTravailFetcher(BaseFetcher):
    """
    Fetcher pour France Travail (ex-Pôle Emploi)
    API: https://francetravail.io/data/api/offres-emploi

    Inscription gratuite sur francetravail.io pour obtenir:
    - Client ID
    - Client Secret

    Multi-recherche pour jobs AWS/Cloud.
    """

    SOURCE_NAME = "francetravail"
    TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
    API_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"

    # Mots-clés pour jobs cloud/AWS
    SEARCH_KEYWORDS = [
        'AWS', 'cloud', 'DevOps', 'Kubernetes', 'Docker',
        'Azure', 'GCP', 'infrastructure', 'SRE', 'Terraform',
        'administrateur système', 'ingénieur cloud', 'architecte cloud',
        'développeur Python', 'développeur backend'
    ]

    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = None
        self._token_expires = None

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def _get_access_token(self) -> Optional[str]:
        """Obtenir un token OAuth2"""
        if not self.is_configured():
            return None

        if self._access_token and self._token_expires:
            if datetime.now() < self._token_expires:
                return self._access_token

        params = {'realm': '/partenaire'}

        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'api_offresdemploiv2 o2dsoffre'
        }

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        response = requests.post(
            self.TOKEN_URL,
            params=params,
            data=data,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()

        token_data = response.json()
        self._access_token = token_data.get('access_token')

        expires_in = token_data.get('expires_in', 1500)
        self._token_expires = datetime.now() + timedelta(seconds=expires_in - 60)

        return self._access_token

    def fetch_jobs(
        self,
        keywords: List[str] = None,
        departement: str = None,
        region: str = None,
        typeContrat: str = None,
        **kwargs
    ) -> List[JobData]:
        """
        Rechercher des offres d'emploi avec multi-mots-clés

        Args:
            keywords: Liste de mots-clés (défaut: SEARCH_KEYWORDS)
            departement: Code département (ex: "75" pour Paris)
            region: Code région
            typeContrat: CDI, CDD, MIS, etc.
        """
        if not self.is_configured():
            return []

        token = self._get_access_token()
        if not token:
            return []

        if keywords is None:
            keywords = self.SEARCH_KEYWORDS

        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }

        all_jobs = {}

        for keyword in keywords:
            try:
                params = {
                    'range': '0-149',  # Max 150 par requête
                    'motsCles': keyword
                }

                if departement:
                    params['departement'] = departement
                if region:
                    params['region'] = region
                if typeContrat:
                    params['typeContrat'] = typeContrat

                response = requests.get(
                    self.API_URL,
                    headers=headers,
                    params=params,
                    timeout=30
                )

                if response.status_code != 200:
                    continue

                data = response.json()
                jobs = data.get('resultats', [])

                for job in jobs:
                    job_id = job.get('id', '')
                    if job_id and job_id not in all_jobs:
                        all_jobs[job_id] = job

            except Exception:
                continue

        return [self.normalize_job(job) for job in all_jobs.values()]

    def normalize_job(self, raw_job: Dict) -> JobData:
        # Type de contrat
        type_contrat = raw_job.get('typeContrat', '')
        job_type_map = {
            'CDI': 'full-time',
            'CDD': 'contract',
            'MIS': 'contract',
            'SAI': 'contract',
            'LIB': 'freelance',
            'REP': 'freelance',
            'FRA': 'freelance',
        }
        job_type = job_type_map.get(type_contrat, 'full-time')

        # Localisation
        lieu = raw_job.get('lieuTravail', {})
        location = lieu.get('libelle', 'France')

        # Salaire
        salaire = raw_job.get('salaire', {})
        salary_text = salaire.get('libelle') if salaire else None

        # Date
        date_creation = raw_job.get('dateCreation')
        posted_at = self._parse_date(date_creation) if date_creation else None

        # Entreprise
        entreprise = raw_job.get('entreprise', {})
        company = entreprise.get('nom', 'Entreprise confidentielle')

        # URL
        url = raw_job.get('origineOffre', {}).get('urlOrigine', '')
        if not url:
            offre_id = raw_job.get('id', '')
            url = f"https://candidat.francetravail.fr/offres/recherche/detail/{offre_id}"

        return JobData(
            external_id=raw_job.get('id', ''),
            title=raw_job.get('intitule', ''),
            company=company,
            description=raw_job.get('description', ''),
            location=location,
            job_type=job_type,
            salary_text=salary_text,
            url=url,
            source_category=raw_job.get('secteurActiviteLibelle', ''),
            posted_at=posted_at,
            tags=[type_contrat] if type_contrat else []
        )
