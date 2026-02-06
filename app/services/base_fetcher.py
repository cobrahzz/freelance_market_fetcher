from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class JobData:
    """Normalized job data structure"""
    external_id: str
    title: str
    company: str
    description: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    salary_text: Optional[str] = None
    url: Optional[str] = None
    company_logo: Optional[str] = None
    source_category: Optional[str] = None
    posted_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)


class BaseFetcher(ABC):
    """Abstract base class for all job fetchers"""

    SOURCE_NAME: str = "unknown"

    @abstractmethod
    def fetch_jobs(self, **kwargs) -> List[JobData]:
        """Fetch jobs from the source. Returns normalized JobData list."""
        pass

    @abstractmethod
    def normalize_job(self, raw_job: Dict) -> JobData:
        """Convert raw API response to normalized JobData."""
        pass

    def get_source_name(self) -> str:
        return self.SOURCE_NAME

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime, handling common formats"""
        if not date_str:
            return None

        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Try ISO format with timezone
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            pass

        return None
