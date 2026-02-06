import csv
import io
from datetime import datetime
from flask import Blueprint, jsonify, request, Response, current_app
from app import db
from app.models import Job, FetchLog

api_bp = Blueprint('api', __name__)


@api_bp.route('/fetch', methods=['POST'])
def fetch_jobs():
    """Trigger job fetch from all or specific sources"""
    from app.services.job_aggregator import JobAggregator

    sources = None
    try:
        if request.is_json and request.json:
            sources = request.json.get('sources')
    except Exception:
        pass  # No JSON body, fetch all sources

    aggregator = JobAggregator(current_app.config)
    results = aggregator.fetch_all(sources=sources)

    total_fetched = 0
    for source_name, result in results.items():
        # Log the fetch
        log = FetchLog(
            source=source_name,
            status=result['status'],
            jobs_fetched=result['count'],
            error_message=result.get('error')
        )
        db.session.add(log)

        # Save jobs to database
        if result['status'] == 'success':
            for job_data in result['jobs']:
                # Check if job already exists
                existing = Job.query.filter_by(
                    source=source_name,
                    external_id=job_data.external_id
                ).first()

                if not existing:
                    job = Job(
                        external_id=job_data.external_id,
                        title=job_data.title,
                        company=job_data.company,
                        description=job_data.description,
                        location=job_data.location,
                        job_type=job_data.job_type,
                        salary_min=job_data.salary_min,
                        salary_max=job_data.salary_max,
                        salary_currency=job_data.salary_currency,
                        salary_text=job_data.salary_text,
                        url=job_data.url,
                        company_logo=job_data.company_logo,
                        source=source_name,
                        source_category=job_data.source_category,
                        posted_at=job_data.posted_at,
                        fetched_at=datetime.utcnow()
                    )
                    db.session.add(job)
                    total_fetched += 1

    db.session.commit()

    return jsonify({
        'status': 'success',
        'results': {k: {'status': v['status'], 'count': v['count'], 'error': v.get('error')} for k, v in results.items()},
        'total_new_jobs': total_fetched
    })


@api_bp.route('/fetch/status')
def fetch_status():
    """Get last fetch status per source"""
    # Get the most recent log for each source
    subquery = db.session.query(
        FetchLog.source,
        db.func.max(FetchLog.fetched_at).label('max_fetched')
    ).group_by(FetchLog.source).subquery()

    logs = db.session.query(FetchLog).join(
        subquery,
        db.and_(
            FetchLog.source == subquery.c.source,
            FetchLog.fetched_at == subquery.c.max_fetched
        )
    ).all()

    return jsonify({
        'sources': {
            log.source: {
                'status': log.status,
                'jobs_fetched': log.jobs_fetched,
                'error': log.error_message,
                'fetched_at': log.fetched_at.isoformat()
            }
            for log in logs
        }
    })


@api_bp.route('/export/csv')
def export_csv():
    """Export filtered jobs to CSV"""
    # Get filter parameters (same as dashboard)
    source = request.args.get('source')
    job_type = request.args.get('job_type')
    search = request.args.get('search')
    bookmarked_only = request.args.get('bookmarked') == 'true'

    # Build query
    query = Job.query

    if source:
        query = query.filter(Job.source == source)
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if search:
        query = query.filter(
            db.or_(
                Job.title.ilike(f'%{search}%'),
                Job.company.ilike(f'%{search}%'),
                Job.description.ilike(f'%{search}%')
            )
        )
    if bookmarked_only:
        query = query.filter(Job.is_bookmarked == True)

    jobs = query.order_by(Job.posted_at.desc().nullslast()).all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'Title', 'Company', 'Location', 'Job Type', 'Salary',
        'URL', 'Source', 'Posted At', 'Bookmarked', 'Applied', 'Notes'
    ])

    # Data
    for job in jobs:
        writer.writerow([
            job.title,
            job.company,
            job.location or '',
            job.job_type or '',
            job.salary_text or '',
            job.url or '',
            job.source,
            job.posted_at.strftime('%Y-%m-%d') if job.posted_at else '',
            'Yes' if job.is_bookmarked else 'No',
            'Yes' if job.is_applied else 'No',
            job.notes or ''
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=jobs_export_{datetime.now().strftime("%Y%m%d")}.csv'}
    )


@api_bp.route('/sources')
def list_sources():
    """List available sources"""
    from app.services.job_aggregator import JobAggregator

    aggregator = JobAggregator(current_app.config)
    sources = [f.SOURCE_NAME for f in aggregator.fetchers]

    return jsonify({
        'sources': sources,
        'manual_entry': True
    })


@api_bp.route('/stats')
def stats():
    """Dashboard statistics"""
    total_jobs = Job.query.count()
    bookmarked = Job.query.filter(Job.is_bookmarked == True).count()
    applied = Job.query.filter(Job.is_applied == True).count()
    manual = Job.query.filter(Job.is_manual == True).count()

    # Jobs per source
    source_counts = db.session.query(
        Job.source, db.func.count(Job.id)
    ).group_by(Job.source).all()

    return jsonify({
        'total_jobs': total_jobs,
        'bookmarked': bookmarked,
        'applied': applied,
        'manual': manual,
        'by_source': {source: count for source, count in source_counts}
    })
