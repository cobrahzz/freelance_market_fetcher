import requests
from typing import List, Dict
from .base_fetcher import BaseFetcher, JobData


class RemotiveFetcher(BaseFetcher):
    """
    Fetcher for Remotive.com
    API: https://remotive.com/api/remote-jobs
    No authentication required.
    Rate limit: 4 requests per day.
    """

    SOURCE_NAME = "remotive"
    API_URL = "https://remotive.com/api/remote-jobs"

    def fetch_jobs(self, category: str = None, **kwargs) -> List[JobData]:
        params = {}
        if category:
            params['category'] = category

        response = requests.get(
            self.API_URL,
            params=params,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        jobs = data.get('jobs', [])

        return [self.normalize_job(job) for job in jobs]

    def normalize_job(self, raw_job: Dict) -> JobData:
        # Map job type
        job_type = raw_job.get('job_type', '').lower()
        if 'full' in job_type:
            job_type = 'full-time'
        elif 'contract' in job_type:
            job_type = 'contract'
        elif 'part' in job_type:
            job_type = 'part-time'
        elif 'freelance' in job_type:
            job_type = 'freelance'
        else:
            job_type = 'remote'

        # Build location string
        location = raw_job.get('candidate_required_location', '')
        if not location:
            location = 'Worldwide'

        return JobData(
            external_id=str(raw_job.get('id', '')),
            title=raw_job.get('title', ''),
            company=raw_job.get('company_name', 'Unknown'),
            description=raw_job.get('description', ''),
            location=location,
            job_type=job_type,
            salary_text=raw_job.get('salary', ''),
            url=raw_job.get('url', ''),
            company_logo=raw_job.get('company_logo', ''),
            source_category=raw_job.get('category', ''),
            posted_at=self._parse_date(raw_job.get('publication_date')),
            tags=raw_job.get('tags', [])
        )
