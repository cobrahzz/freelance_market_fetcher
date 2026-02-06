from typing import List, Dict
from .base_fetcher import BaseFetcher, JobData
from .remoteok_fetcher import RemoteOKFetcher
from .remotive_fetcher import RemotiveFetcher
from .arbeitnow_fetcher import ArbeitnowFetcher
from .himalayas_fetcher import HimalayasFetcher
from .adzuna_fetcher import AdzunaFetcher
from .francetravail_fetcher import FranceTravailFetcher
from .careerjet_fetcher import CareerjetFetcher


class JobAggregator:
    """Coordinates fetching from multiple sources"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.fetchers: List[BaseFetcher] = []
        self._initialize_fetchers()

    def _initialize_fetchers(self):
        """Initialize all available fetchers"""
        # International sources (no auth required)
        self.fetchers.append(RemoteOKFetcher())
        self.fetchers.append(RemotiveFetcher())
        self.fetchers.append(ArbeitnowFetcher())
        self.fetchers.append(HimalayasFetcher())

        # France Travail (ex-Pôle Emploi) - needs OAuth2 credentials
        ft_client_id = self.config.get('FRANCETRAVAIL_CLIENT_ID')
        ft_client_secret = self.config.get('FRANCETRAVAIL_CLIENT_SECRET')
        if ft_client_id and ft_client_secret:
            self.fetchers.append(FranceTravailFetcher(
                client_id=ft_client_id,
                client_secret=ft_client_secret
            ))

        # Careerjet - needs affiliate ID
        careerjet_affid = self.config.get('CAREERJET_AFFID')
        if careerjet_affid:
            self.fetchers.append(CareerjetFetcher(affid=careerjet_affid))

        # Adzuna - needs app_id and api_key
        adzuna_app_id = self.config.get('ADZUNA_APP_ID')
        adzuna_api_key = self.config.get('ADZUNA_API_KEY')
        if adzuna_app_id and adzuna_api_key:
            self.fetchers.append(AdzunaFetcher(
                app_id=adzuna_app_id,
                api_key=adzuna_api_key
            ))

    def _needs_config(self, fetcher: BaseFetcher) -> bool:
        """Check if a fetcher needs configuration"""
        if hasattr(fetcher, 'is_configured'):
            return not fetcher.is_configured()
        return False

    def fetch_all(self, sources: List[str] = None) -> Dict[str, Dict]:
        """
        Fetch from all or specified sources

        Args:
            sources: Optional list of source names to fetch from.
                    If None, fetches from all sources.

        Returns:
            Dict with source names as keys, containing:
            - status: 'success' or 'error'
            - jobs: List of JobData objects
            - count: Number of jobs fetched
            - error: Error message if status is 'error'
        """
        results = {}

        for fetcher in self.fetchers:
            source_name = fetcher.SOURCE_NAME

            # Skip if specific sources requested and this isn't one of them
            if sources and source_name not in sources:
                continue

            # Skip if not configured
            if self._needs_config(fetcher):
                results[source_name] = {
                    'status': 'skipped',
                    'jobs': [],
                    'count': 0,
                    'error': 'Non configuré - clés API manquantes'
                }
                continue

            try:
                jobs = fetcher.fetch_jobs()
                results[source_name] = {
                    'status': 'success',
                    'jobs': jobs,
                    'count': len(jobs)
                }
            except Exception as e:
                results[source_name] = {
                    'status': 'error',
                    'jobs': [],
                    'count': 0,
                    'error': str(e)
                }

        return results

    def fetch_source(self, source_name: str, **kwargs) -> Dict:
        """Fetch from a specific source"""
        for fetcher in self.fetchers:
            if fetcher.SOURCE_NAME == source_name:
                if self._needs_config(fetcher):
                    return {
                        'status': 'error',
                        'jobs': [],
                        'count': 0,
                        'error': 'Non configuré - clés API manquantes'
                    }

                try:
                    jobs = fetcher.fetch_jobs(**kwargs)
                    return {
                        'status': 'success',
                        'jobs': jobs,
                        'count': len(jobs)
                    }
                except Exception as e:
                    return {
                        'status': 'error',
                        'jobs': [],
                        'count': 0,
                        'error': str(e)
                    }

        return {
            'status': 'error',
            'jobs': [],
            'count': 0,
            'error': f'Source inconnue: {source_name}'
        }

    def get_available_sources(self) -> List[str]:
        """Get list of available source names"""
        sources = []
        for fetcher in self.fetchers:
            if not self._needs_config(fetcher):
                sources.append(fetcher.SOURCE_NAME)
        return sources

    def get_all_sources(self) -> List[Dict]:
        """Get all sources with their configuration status"""
        return [
            {
                'name': f.SOURCE_NAME,
                'configured': not self._needs_config(f)
            }
            for f in self.fetchers
        ]
