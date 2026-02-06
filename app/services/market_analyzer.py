import re
from collections import Counter
from typing import Dict, List, Tuple, Optional
from app.models import Job


# Technologies à détecter (insensible à la casse)
TECHNOLOGIES = [
    # Langages
    'Python', 'JavaScript', 'TypeScript', 'Java', 'C#', 'C++', 'PHP', 'Ruby', 'Go', 'Rust',
    'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'Perl', 'Shell', 'Bash', 'PowerShell',

    # Frontend
    'React', 'Angular', 'Vue', 'Vue.js', 'Svelte', 'Next.js', 'Nuxt', 'jQuery',
    'HTML', 'CSS', 'SASS', 'SCSS', 'Tailwind', 'Bootstrap', 'Material UI',

    # Backend
    'Node.js', 'Express', 'Django', 'Flask', 'FastAPI', 'Spring', 'Spring Boot',
    '.NET', 'ASP.NET', 'Laravel', 'Symfony', 'Rails', 'Ruby on Rails',

    # Data & ML
    'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn', 'Pandas', 'NumPy',
    'Spark', 'Hadoop', 'Kafka', 'Airflow', 'DBT',

    # Databases
    'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch',
    'Oracle', 'SQL Server', 'SQLite', 'Cassandra', 'DynamoDB', 'Neo4j',

    # Cloud & DevOps
    'AWS', 'Azure', 'GCP', 'Google Cloud', 'Docker', 'Kubernetes', 'K8s',
    'Terraform', 'Ansible', 'Jenkins', 'GitLab CI', 'GitHub Actions',
    'Linux', 'Nginx', 'Apache',

    # Mobile
    'React Native', 'Flutter', 'iOS', 'Android', 'Xamarin',

    # Autres
    'Git', 'GraphQL', 'REST', 'API', 'Microservices', 'Agile', 'Scrum',
    'CI/CD', 'DevOps', 'SAP', 'Salesforce', 'Power BI', 'Tableau',
]

# Patterns pour détecter l'expérience
EXPERIENCE_PATTERNS = [
    r'(\d+)\s*(?:à|-)?\s*(\d+)?\s*(?:ans?|années?)\s*(?:d\')?exp[ée]rience',
    r'exp[ée]rience\s*(?:de\s*)?(\d+)\s*(?:à|-)?\s*(\d+)?\s*(?:ans?|années?)',
    r'(\d+)\+?\s*(?:ans?|années?|years?)\s*(?:of\s*)?experience',
    r'experience[:\s]*(\d+)\s*(?:à|-)?\s*(\d+)?\s*(?:ans?|années?|years?)',
    r'(\d+)\s*(?:ans?|années?)\s*minimum',
    r'junior|débutant|entry.?level',  # 0-2 ans
    r'confirmé|intermédiaire|mid.?level',  # 3-5 ans
    r'senior|expert|lead',  # 5+ ans
]

# Diplômes à détecter
DIPLOMAS = {
    'Bac+5 / Master': [
        r'bac\s*\+\s*5', r'master', r'ingénieur', r'école d\'ingénieur',
        r'msc', r'm\.sc', r'mba', r'mastère', r'diplôme d\'ingénieur'
    ],
    'Bac+3 / Licence': [
        r'bac\s*\+\s*3', r'licence', r'bachelor', r'but', r'dut', r'bts'
    ],
    'Bac+2': [
        r'bac\s*\+\s*2', r'deug', r'bts', r'dut'
    ],
    'Bac+8 / Doctorat': [
        r'bac\s*\+\s*8', r'doctorat', r'phd', r'thèse'
    ],
    'Autodidacte accepté': [
        r'autodidacte', r'self.?taught', r'sans diplôme', r'bootcamp'
    ]
}


class MarketAnalyzer:
    """Analyse le marché à partir des offres d'emploi"""

    def __init__(self, jobs: List[Job] = None):
        self.jobs = jobs or []

    def set_jobs(self, jobs: List[Job]):
        self.jobs = jobs

    def analyze_technologies(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Compte les technologies mentionnées dans les offres"""
        tech_counter = Counter()

        for job in self.jobs:
            text = f"{job.title} {job.description or ''} {job.source_category or ''}"
            text_lower = text.lower()

            found_techs = set()  # Éviter les doublons par offre
            for tech in TECHNOLOGIES:
                # Recherche avec word boundaries
                pattern = r'\b' + re.escape(tech.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    # Normaliser certains noms
                    normalized = self._normalize_tech(tech)
                    found_techs.add(normalized)

            for tech in found_techs:
                tech_counter[tech] += 1

        return tech_counter.most_common(limit)

    def _normalize_tech(self, tech: str) -> str:
        """Normalise les noms de technologies"""
        normalizations = {
            'vue.js': 'Vue.js',
            'vue': 'Vue.js',
            'node.js': 'Node.js',
            'react native': 'React Native',
            'ruby on rails': 'Rails',
            'rails': 'Rails',
            'k8s': 'Kubernetes',
            'gcp': 'Google Cloud',
            'google cloud': 'Google Cloud',
            'spring boot': 'Spring Boot',
            'spring': 'Spring',
        }
        return normalizations.get(tech.lower(), tech)

    def analyze_salaries(self) -> Dict:
        """Analyse les salaires et calcule les moyennes"""
        hourly_rates = []
        daily_rates = []
        monthly_rates = []
        yearly_rates = []

        for job in self.jobs:
            salary_text = job.salary_text or ''
            salary_min = job.salary_min
            salary_max = job.salary_max

            # Parser le texte du salaire
            parsed = self._parse_salary(salary_text, salary_min, salary_max)
            if parsed:
                rate_type, min_val, max_val = parsed
                avg = (min_val + max_val) / 2 if max_val else min_val

                if rate_type == 'hourly':
                    hourly_rates.append(avg)
                elif rate_type == 'daily':
                    daily_rates.append(avg)
                elif rate_type == 'monthly':
                    monthly_rates.append(avg)
                elif rate_type == 'yearly':
                    yearly_rates.append(avg)

        # Convertir tout en différentes unités
        all_yearly = []

        # Convertir les taux horaires en annuel (1600h/an pour freelance)
        for h in hourly_rates:
            all_yearly.append(h * 1600)

        # Convertir les taux journaliers en annuel (218 jours/an)
        for d in daily_rates:
            all_yearly.append(d * 218)

        # Convertir les taux mensuels en annuel
        for m in monthly_rates:
            all_yearly.append(m * 12)

        # Ajouter les annuels directement
        all_yearly.extend(yearly_rates)

        if not all_yearly:
            return {
                'hourly': None,
                'daily': None,
                'monthly': None,
                'yearly': None,
                'sample_size': 0
            }

        avg_yearly = sum(all_yearly) / len(all_yearly)

        return {
            'hourly': round(avg_yearly / 1600, 2),
            'daily': round(avg_yearly / 218, 2),
            'monthly': round(avg_yearly / 12, 2),
            'yearly': round(avg_yearly, 2),
            'sample_size': len(all_yearly),
            'raw_counts': {
                'hourly': len(hourly_rates),
                'daily': len(daily_rates),
                'monthly': len(monthly_rates),
                'yearly': len(yearly_rates)
            }
        }

    def _parse_salary(self, text: str, sal_min: int = None, sal_max: int = None) -> Optional[Tuple[str, float, float]]:
        """Parse le salaire depuis le texte ou les valeurs min/max"""
        text_lower = text.lower()

        # Patterns pour détecter le type de salaire
        patterns = {
            'hourly': [r'(\d+(?:[.,]\d+)?)\s*(?:€|eur|euros?)?\s*/?\s*(?:h|heure|hour)', r'(\d+(?:[.,]\d+)?)\s*€/h'],
            'daily': [r'(\d+(?:[.,]\d+)?)\s*(?:€|eur|euros?)?\s*/?\s*(?:j|jour|day|tjm)', r'tjm[:\s]*(\d+)'],
            'monthly': [r'(\d+(?:[.,]\d+)?)\s*(?:€|eur|euros?)?\s*/?\s*(?:mois|month)', r'(\d+)k?\s*(?:€|eur)?\s*/\s*mois'],
            'yearly': [r'(\d+(?:[.,]\d+)?)\s*k?\s*(?:€|eur|euros?)?\s*/?\s*(?:an|year|annuel)', r'(\d+)k?\s*(?:€|eur)?\s*/\s*an'],
        }

        for rate_type, pats in patterns.items():
            for pattern in pats:
                match = re.search(pattern, text_lower)
                if match:
                    value = float(match.group(1).replace(',', '.'))
                    # Gérer les valeurs en k (milliers)
                    if 'k' in text_lower and value < 1000:
                        value *= 1000
                    return (rate_type, value, value)

        # Utiliser les valeurs min/max si disponibles
        if sal_min or sal_max:
            min_val = sal_min or sal_max
            max_val = sal_max or sal_min

            # Deviner le type basé sur la valeur
            avg = (min_val + max_val) / 2
            if avg < 100:
                return ('hourly', min_val, max_val)
            elif avg < 1500:
                return ('daily', min_val, max_val)
            elif avg < 15000:
                return ('monthly', min_val, max_val)
            else:
                return ('yearly', min_val, max_val)

        # Chercher juste un nombre avec € dans le texte
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:k)?\s*(?:€|eur)', text_lower)
        if match:
            value = float(match.group(1).replace(',', '.'))
            if 'k' in text_lower and value < 1000:
                value *= 1000

            # Deviner le type
            if value < 100:
                return ('hourly', value, value)
            elif value < 1500:
                return ('daily', value, value)
            elif value < 15000:
                return ('monthly', value, value)
            else:
                return ('yearly', value, value)

        return None

    def analyze_experience(self) -> Dict:
        """Analyse les années d'expérience requises"""
        experience_years = []
        levels = Counter()

        for job in self.jobs:
            text = f"{job.title} {job.description or ''}"
            text_lower = text.lower()

            # Chercher les patterns d'expérience
            for pattern in EXPERIENCE_PATTERNS[:5]:  # Patterns numériques
                match = re.search(pattern, text_lower)
                if match:
                    min_years = int(match.group(1))
                    max_years = int(match.group(2)) if match.lastindex >= 2 and match.group(2) else min_years
                    experience_years.append((min_years + max_years) / 2)
                    break

            # Détecter le niveau
            if re.search(r'junior|débutant|entry.?level|0.?2\s*ans', text_lower):
                levels['Junior (0-2 ans)'] += 1
            elif re.search(r'confirmé|intermédiaire|mid.?level|3.?5\s*ans', text_lower):
                levels['Confirmé (3-5 ans)'] += 1
            elif re.search(r'senior|expert|lead|5\+?\s*ans|7\+?\s*ans|10\+?\s*ans', text_lower):
                levels['Senior (5+ ans)'] += 1

        avg_years = sum(experience_years) / len(experience_years) if experience_years else None

        return {
            'average_years': round(avg_years, 1) if avg_years else None,
            'sample_size': len(experience_years),
            'levels': dict(levels.most_common()),
            'distribution': {
                '0-2 ans': len([x for x in experience_years if x <= 2]),
                '3-5 ans': len([x for x in experience_years if 2 < x <= 5]),
                '5-10 ans': len([x for x in experience_years if 5 < x <= 10]),
                '10+ ans': len([x for x in experience_years if x > 10]),
            }
        }

    def analyze_education(self) -> Dict:
        """Analyse les diplômes requis"""
        diploma_counter = Counter()

        for job in self.jobs:
            text = f"{job.title} {job.description or ''}"
            text_lower = text.lower()

            for diploma_name, patterns in DIPLOMAS.items():
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        diploma_counter[diploma_name] += 1
                        break  # Ne compter qu'une fois par diplôme

        return {
            'distribution': dict(diploma_counter.most_common()),
            'total_with_requirement': sum(diploma_counter.values()),
            'total_jobs': len(self.jobs)
        }

    def get_full_analysis(self) -> Dict:
        """Retourne l'analyse complète du marché"""
        return {
            'technologies': self.analyze_technologies(20),
            'salaries': self.analyze_salaries(),
            'experience': self.analyze_experience(),
            'education': self.analyze_education(),
            'total_jobs': len(self.jobs)
        }
