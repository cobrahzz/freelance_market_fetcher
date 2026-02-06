import requests
from datetime import datetime
from typing import List, Dict
from .base_fetcher import BaseFetcher, JobData


class ArbeitnowFetcher(BaseFetcher):
    """
    Fetcher for Arbeitnow.com
    API: https://www.arbeitnow.com/api/job-board-api
    No authentication required.
    Free job board API with jobs from ATS systems.
    """

    SOURCE_NAME = "arbeitnow"
    API_URL = "https://www.arbeitnow.com/api/job-board-api"

    def fetch_jobs(self, **kwargs) -> List[JobData]:
        response = requests.get(
            self.API_URL,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        jobs = data.get('data', [])

        return [self.normalize_job(job) for job in jobs]

    def normalize_job(self, raw_job: Dict) -> JobData:
        # Determine job type from tags
        tags = raw_job.get('tags', [])
        job_type = 'full-time'

        tags_lower = [t.lower() for t in tags]
        if 'remote' in tags_lower:
            job_type = 'remote'
        elif 'contract' in tags_lower or 'freelance' in tags_lower:
            job_type = 'contract'
        elif 'part-time' in tags_lower or 'part time' in tags_lower:
            job_type = 'part-time'

        # Check if remote
        remote = raw_job.get('remote', False)
        if remote:
            job_type = 'remote'

        # Handle created_at - can be timestamp or string
        posted_at = None
        created_at = raw_job.get('created_at')
        if created_at:
            if isinstance(created_at, int):
                posted_at = datetime.fromtimestamp(created_at)
            else:
                posted_at = self._parse_date(created_at)

        return JobData(
            external_id=raw_job.get('slug', ''),
            title=raw_job.get('title', ''),
            company=raw_job.get('company_name', 'Unknown'),
            description=raw_job.get('description', ''),
            location=raw_job.get('location', ''),
            job_type=job_type,
            url=raw_job.get('url', ''),
            source_category=','.join(tags),
            posted_at=posted_at,
            tags=tags
        )
