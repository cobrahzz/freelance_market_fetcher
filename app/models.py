from datetime import datetime
from app import db


# Association table for job-tag many-to-many
job_tags = db.Table(
    'job_tags',
    db.Column('job_id', db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)

    # Core fields
    external_id = db.Column(db.String(255), nullable=True)
    title = db.Column(db.String(500), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Location & type
    location = db.Column(db.String(255), nullable=True)
    job_type = db.Column(db.String(50), nullable=True)

    # Compensation
    salary_min = db.Column(db.Integer, nullable=True)
    salary_max = db.Column(db.Integer, nullable=True)
    salary_currency = db.Column(db.String(10), nullable=True)
    salary_text = db.Column(db.String(255), nullable=True)

    # URLs
    url = db.Column(db.String(1000), nullable=True)
    company_logo = db.Column(db.String(1000), nullable=True)

    # Source tracking
    source = db.Column(db.String(50), nullable=False)
    source_category = db.Column(db.String(255), nullable=True)

    # User interaction
    is_manual = db.Column(db.Boolean, default=False)
    is_bookmarked = db.Column(db.Boolean, default=False)
    is_applied = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)

    # Timestamps
    posted_at = db.Column(db.DateTime, nullable=True)
    fetched_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tags = db.relationship('Tag', secondary=job_tags, backref=db.backref('jobs', lazy='dynamic'))

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('source', 'external_id', name='uq_source_external_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'external_id': self.external_id,
            'title': self.title,
            'company': self.company,
            'description': self.description,
            'location': self.location,
            'job_type': self.job_type,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'salary_currency': self.salary_currency,
            'salary_text': self.salary_text,
            'url': self.url,
            'company_logo': self.company_logo,
            'source': self.source,
            'source_category': self.source_category,
            'is_manual': self.is_manual,
            'is_bookmarked': self.is_bookmarked,
            'is_applied': self.is_applied,
            'notes': self.notes,
            'posted_at': self.posted_at.isoformat() if self.posted_at else None,
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'tags': [tag.name for tag in self.tags]
        }


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'


class FetchLog(db.Model):
    __tablename__ = 'fetch_logs'

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    jobs_fetched = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FetchLog {self.source} - {self.status}>'
