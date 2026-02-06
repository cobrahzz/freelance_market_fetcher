import requests
from typing import List, Dict
from .base_fetcher import BaseFetcher, JobData


class RemoteOKFetcher(BaseFetcher):
    """
    Fetcher for RemoteOK.com
    API: https://remoteok.com/api
    Supports tag filtering: /api?tag=devops
    """

    SOURCE_NAME = "remoteok"
    API_URL = "https://remoteok.com/api"

    # Tags to fetch for cloud/AWS jobs
    CLOUD_TAGS = ['devops', 'cloud', 'aws', 'sysadmin', 'backend', 'infra']

    def fetch_jobs(self, tags: List[str] = None, **kwargs) -> List[JobData]:
        headers = {
            'User-Agent': 'FreelanceJobFetcher/1.0'
        }

        all_jobs = {}

        # If no tags specified, use cloud tags + general fetch
        if tags is None:
            tags = self.CLOUD_TAGS + [None]  # None = all jobs

        for tag in tags:
            try:
                url = self.API_URL
                if tag:
                    url = f"{self.API_URL}?tag={tag}"

                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()

                # First item is legal notice, skip it
                jobs = data[1:] if data and len(data) > 1 else []

                for job in jobs:
                    if job.get('position') and job.get('id'):
                        job_id = str(job.get('id'))
                        if job_id not in all_jobs:
                            all_jobs[job_id] = job

            except Exception:
                continue

        return [self.normalize_job(job) for job in all_jobs.values()]

    def normalize_job(self, raw_job: Dict) -> JobData:
        salary_text = None
        salary_min = raw_job.get('salary_min')
        salary_max = raw_job.get('salary_max')

        if salary_min and salary_max:
            salary_text = f"${salary_min:,} - ${salary_max:,}"
        elif salary_min:
            salary_text = f"${salary_min:,}+"
        elif salary_max:
            salary_text = f"Up to ${salary_max:,}"

        return JobData(
            external_id=str(raw_job.get('id', '')),
            title=raw_job.get('position', ''),
            company=raw_job.get('company', 'Unknown'),
            description=raw_job.get('description', ''),
            location=raw_job.get('location') or 'Remote',
            job_type='remote',
            salary_min=salary_min,
            salary_max=salary_max,
            salary_text=salary_text,
            url=raw_job.get('url', ''),
            company_logo=raw_job.get('company_logo', ''),
            source_category=','.join(raw_job.get('tags', [])),
            posted_at=self._parse_date(raw_job.get('date')),
            tags=raw_job.get('tags', [])
        )
