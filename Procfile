web: gunicorn careergraph.wsgi --log-file -
worker: celery -A careergraph worker --loglevel=info
beat: celery -A careergraph beat --loglevel=info