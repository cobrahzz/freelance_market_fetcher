import requests
from datetime import datetime
from typing import List, Dict
from .base_fetcher import BaseFetcher, JobData


class HimalayasFetcher(BaseFetcher):
    """
    Fetcher for Himalayas.app
    API: https://himalayas.app/jobs/api
    Free, no auth required. Good for remote tech/cloud jobs.
    """

    SOURCE_NAME = "himalayas"
    API_URL = "https://himalayas.app/jobs/api"

    def fetch_jobs(self, limit: int = 500, **kwargs) -> List[JobData]:
        headers = {
            'User-Agent': 'FreelanceJobFetcher/1.0'
        }

        params = {
            'limit': limit
        }

        response = requests.get(
            self.API_URL,
            headers=headers,
            params=params,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()
        jobs = data.get('jobs', [])

        return [self.normalize_job(job) for job in jobs]

    def normalize_job(self, raw_job: Dict) -> JobData:
        # Salary
        salary_text = None
        salary_min = raw_job.get('minSalary')
        salary_max = raw_job.get('maxSalary')
        currency = raw_job.get('currency', 'USD')

        if salary_min and salary_max:
            salary_text = f"{int(salary_min):,} - {int(salary_max):,} {currency}"
        elif salary_min:
            salary_text = f"{int(salary_min):,}+ {currency}"

        # Categories/tags (list of strings)
        categories = raw_job.get('categories', [])
        tags = [c for c in categories if isinstance(c, str)]

        # Location
        location_req = raw_job.get('locationRestrictions', [])
        if location_req:
            location = ', '.join(location_req[:3])
        else:
            location = 'Worldwide Remote'

        # Parse pubDate (Unix timestamp)
        posted_at = None
        pub_date = raw_job.get('pubDate')
        if pub_date and isinstance(pub_date, int):
            try:
                posted_at = datetime.fromtimestamp(pub_date)
            except:
                pass

        # External ID from guid
        external_id = raw_job.get('guid', '') or raw_job.get('applicationLink', '')

        return JobData(
            external_id=str(hash(external_id)),
            title=raw_job.get('title', ''),
            company=raw_job.get('companyName', 'Unknown'),
            description=raw_job.get('excerpt', '') or raw_job.get('description', ''),
            location=location,
            job_type='remote',
            salary_min=int(salary_min) if salary_min else None,
            salary_max=int(salary_max) if salary_max else None,
            salary_text=salary_text,
            url=raw_job.get('applicationLink') or raw_job.get('guid', ''),
            company_logo=raw_job.get('companyLogo', ''),
            source_category=','.join(tags[:5]),  # First 5 tags
            posted_at=posted_at,
            tags=tags
        )
