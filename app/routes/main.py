from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Job, FetchLog

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def dashboard():
    """Main dashboard with job listings"""
    # Get filter parameters
    source = request.args.get('source')
    job_type = request.args.get('job_type')
    search = request.args.get('search')
    bookmarked_only = request.args.get('bookmarked') == 'true'
    applied_only = request.args.get('applied') == 'true'

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
    if applied_only:
        query = query.filter(Job.is_applied == True)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20

    jobs = query.order_by(Job.posted_at.desc().nullslast(), Job.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Get sources for filter dropdown
    sources = db.session.query(Job.source).distinct().all()

    # Get last fetch time
    last_fetch = FetchLog.query.order_by(FetchLog.fetched_at.desc()).first()

    return render_template(
        'dashboard.html',
        jobs=jobs,
        sources=[s[0] for s in sources],
        last_fetch=last_fetch,
        current_filters={
            'source': source,
            'job_type': job_type,
            'search': search or '',
            'bookmarked': bookmarked_only,
            'applied': applied_only
        }
    )


@main_bp.route('/jobs/new', methods=['GET', 'POST'])
def new_job():
    """Manual job entry form"""
    if request.method == 'POST':
        job = Job(
            title=request.form['title'],
            company=request.form['company'],
            description=request.form.get('description'),
            location=request.form.get('location'),
            job_type=request.form.get('job_type'),
            url=request.form.get('url'),
            salary_text=request.form.get('salary'),
            source='manual',
            is_manual=True,
            notes=request.form.get('notes')
        )
        db.session.add(job)
        db.session.commit()
        flash('Job added successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('job_form.html', job=None)


@main_bp.route('/jobs/<int:job_id>')
def job_detail(job_id):
    """Single job detail view"""
    job = Job.query.get_or_404(job_id)
    return render_template('job_detail.html', job=job)


@main_bp.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    """Edit job form"""
    job = Job.query.get_or_404(job_id)

    if request.method == 'POST':
        job.title = request.form['title']
        job.company = request.form['company']
        job.description = request.form.get('description')
        job.location = request.form.get('location')
        job.job_type = request.form.get('job_type')
        job.url = request.form.get('url')
        job.salary_text = request.form.get('salary')
        job.notes = request.form.get('notes')
        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('main.job_detail', job_id=job.id))

    return render_template('job_form.html', job=job)


@main_bp.route('/jobs/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    """Delete a job"""
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted.', 'info')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/jobs/<int:job_id>/bookmark', methods=['POST'])
def toggle_bookmark(job_id):
    """Toggle bookmark status"""
    job = Job.query.get_or_404(job_id)
    job.is_bookmarked = not job.is_bookmarked
    db.session.commit()
    return redirect(request.referrer or url_for('main.dashboard'))


@main_bp.route('/jobs/<int:job_id>/applied', methods=['POST'])
def toggle_applied(job_id):
    """Toggle applied status"""
    job = Job.query.get_or_404(job_id)
    job.is_applied = not job.is_applied
    db.session.commit()
    return redirect(request.referrer or url_for('main.dashboard'))


@main_bp.route('/analytics')
def analytics():
    """Market analytics dashboard"""
    from app.services.market_analyzer import MarketAnalyzer

    # Get all jobs for analysis
    jobs = Job.query.all()

    analyzer = MarketAnalyzer(jobs)
    analysis = analyzer.get_full_analysis()

    return render_template('analytics.html', analysis=analysis)
