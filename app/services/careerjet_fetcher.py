import requests
from typing import List, Dict
from urllib.parse import urlencode
from .base_fetcher import BaseFetcher, JobData


class CareerjetFetcher(BaseFetcher):
    """
    Fetcher pour Careerjet (Optioncarriere en France)
    API: https://www.careerjet.com/partners/api/

    Inscription gratuite requise pour obtenir une clé API.
    Bonne couverture des offres françaises.
    """

    SOURCE_NAME = "careerjet"
    API_URL = "https://public.api.careerjet.net/search"

    def __init__(self, affid: str = None):
        """
        Args:
            affid: Affiliate ID (clé API) obtenu sur careerjet.com/partners
        """
        self.affid = affid

    def is_configured(self) -> bool:
        return bool(self.affid)

    def fetch_jobs(
        self,
        keywords: str = "développeur",
        location: str = "france",
        pagesize: int = 99,
        page: int = 1,
        contracttype: str = None,
        **kwargs
    ) -> List[JobData]:
        """
        Rechercher des offres

        Args:
            keywords: Mots-clés de recherche
            location: Lieu (ville, région, pays)
            pagesize: Nombre de résultats (max 99)
            page: Numéro de page
            contracttype: 'p' (permanent/CDI), 'c' (contract/CDD), etc.
        """
        if not self.is_configured():
            return []

        params = {
            'affid': self.affid,
            'locale_code': 'fr_FR',
            'keywords': keywords,
            'location': location,
            'pagesize': pagesize,
            'page': page,
            'sort': 'date',  # Tri par date
        }

        if contracttype:
            params['contracttype'] = contracttype

        response = requests.get(
            self.API_URL,
            params=params,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()

        if data.get('type') == 'JOBS':
            jobs = data.get('jobs', [])
            return [self.normalize_job(job) for job in jobs]

        return []

    def normalize_job(self, raw_job: Dict) -> JobData:
        # Type de contrat
        job_type = 'full-time'
        contract_type = raw_job.get('contracttype', '')
        if contract_type == 'c':
            job_type = 'contract'
        elif contract_type == 'p':
            job_type = 'full-time'
        elif contract_type == 't':
            job_type = 'part-time'

        # Salaire
        salary = raw_job.get('salary', '')

        return JobData(
            external_id=str(hash(raw_job.get('url', ''))),
            title=raw_job.get('title', ''),
            company=raw_job.get('company', 'Non spécifié'),
            description=raw_job.get('description', ''),
            location=raw_job.get('locations', ''),
            job_type=job_type,
            salary_text=salary if salary else None,
            url=raw_job.get('url', ''),
            source_category=raw_job.get('site', ''),
            posted_at=self._parse_date(raw_job.get('date')),
            tags=[]
        )
