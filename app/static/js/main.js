document.addEventListener('DOMContentLoaded', function() {
    // Fetch buttons
    const fetchAllBtn = document.getElementById('fetch-all');
    const fetchEmptyBtn = document.getElementById('fetch-empty');
    const fetchModal = document.getElementById('fetch-modal');
    const fetchProgress = document.getElementById('fetch-progress');

    function fetchJobs() {
        if (fetchModal) {
            fetchModal.style.display = 'flex';
        }

        fetch('/api/fetch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                let message = `Fetched ${data.total_new_jobs} new jobs.`;

                // Show details per source
                const details = Object.entries(data.results)
                    .map(([source, result]) => `${source}: ${result.count}`)
                    .join(', ');

                if (fetchProgress) {
                    fetchProgress.textContent = message + ' (' + details + ')';
                }

                // Reload page after short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                throw new Error('Fetch failed');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (fetchProgress) {
                fetchProgress.textContent = 'Error fetching jobs. Please try again.';
            }
            setTimeout(() => {
                if (fetchModal) {
                    fetchModal.style.display = 'none';
                }
            }, 2000);
        });
    }

    if (fetchAllBtn) {
        fetchAllBtn.addEventListener('click', fetchJobs);
    }

    if (fetchEmptyBtn) {
        fetchEmptyBtn.addEventListener('click', fetchJobs);
    }

    // Auto-submit filters on change (optional enhancement)
    const filterSelects = document.querySelectorAll('.filters select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            this.form.submit();
        });
    });

    // Confirm delete
    const deleteForms = document.querySelectorAll('form[action*="/delete"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this job?')) {
                e.preventDefault();
            }
        });
    });
});
