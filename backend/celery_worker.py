from backend.app import create_app
import backend.tasks

app = create_app()
celery = app.extensions["celery"]
