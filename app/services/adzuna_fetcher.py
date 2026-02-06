import requests
from typing import List, Dict
from .base_fetcher import BaseFetcher, JobData


class AdzunaFetcher(BaseFetcher):
    """
    Fetcher for Adzuna.com
    API: https://developer.adzuna.com/
    Requires app_id and api_key (free registration).
    Multi-search for AWS/Cloud jobs in France.
    """

    SOURCE_NAME = "adzuna"
    API_URL = "https://api.adzuna.com/v1/api/jobs"

    # Keywords to search for cloud/AWS jobs
    SEARCH_KEYWORDS = [
        'AWS', 'cloud', 'DevOps', 'Kubernetes', 'Docker',
        'Azure', 'GCP', 'infrastructure', 'SRE',
        'développeur Python', 'ingénieur cloud'
    ]

    def __init__(self, app_id: str = None, api_key: str = None):
        self.app_id = app_id
        self.api_key = api_key

    def is_configured(self) -> bool:
        return bool(self.app_id and self.api_key)

    def fetch_jobs(
        self,
        country: str = 'fr',
        keywords: List[str] = None,
        results_per_page: int = 50,
        **kwargs
    ) -> List[JobData]:
        if not self.is_configured():
            return []

        if keywords is None:
            keywords = self.SEARCH_KEYWORDS

        all_jobs = {}

        for keyword in keywords:
            try:
                # Search multiple pages
                for page in [1, 2]:
                    url = f"{self.API_URL}/{country}/search/{page}"

                    params = {
                        'app_id': self.app_id,
                        'app_key': self.api_key,
                        'results_per_page': results_per_page,
                        'what': keyword,
                        'content-type': 'application/json'
                    }

                    response = requests.get(url, params=params, timeout=30)
                    if response.status_code != 200:
                        continue

                    data = response.json()
                    jobs = data.get('results', [])

                    for job in jobs:
                        job_id = str(job.get('id', ''))
                        if job_id and job_id not in all_jobs:
                            all_jobs[job_id] = job

            except Exception:
                continue

        return [self.normalize_job(job) for job in all_jobs.values()]

    def normalize_job(self, raw_job: Dict) -> JobData:
        salary_min = raw_job.get('salary_min')
        salary_max = raw_job.get('salary_max')
        salary_text = None

        if salary_min and salary_max:
            salary_text = f"{int(salary_min):,} - {int(salary_max):,} EUR"
        elif salary_min:
            salary_text = f"{int(salary_min):,}+ EUR"

        # Location
        location_data = raw_job.get('location', {})
        location_parts = []
        for area in location_data.get('area', []):
            location_parts.append(area)
        location = ', '.join(location_parts) if location_parts else 'France'

        # Job type
        contract_type = raw_job.get('contract_type', '')
        contract_time = raw_job.get('contract_time', '')

        job_type = 'full-time'
        if 'contract' in contract_type.lower():
            job_type = 'contract'
        elif 'part' in contract_time.lower():
            job_type = 'part-time'

        return JobData(
            external_id=str(raw_job.get('id', '')),
            title=raw_job.get('title', ''),
            company=raw_job.get('company', {}).get('display_name', 'Unknown'),
            description=raw_job.get('description', ''),
            location=location,
            job_type=job_type,
            salary_min=int(salary_min) if salary_min else None,
            salary_max=int(salary_max) if salary_max else None,
            salary_text=salary_text,
            url=raw_job.get('redirect_url', ''),
            source_category=raw_job.get('category', {}).get('label', ''),
            posted_at=self._parse_date(raw_job.get('created')),
            tags=[]
        )
