import os
from flask import Flask
from flask_cors import CORS
from celery import Celery, Task
from werkzeug.security import generate_password_hash
from backend.models import db, cache, User, CompanyProfile, StudentProfile, PlacementDrive, Application, Notification, Placement

# celery setup
def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

# create the app
def create_app():
    app = Flask(__name__, 
                template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '../templates')),
                static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/src')))
    
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../instance/ppa_portal.db'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'super-secret-mvp-key'

    # redis cache
    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'

    # celery config
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost:6379/0",
            result_backend="redis://localhost:6379/0",
            timezone="Asia/Kolkata",
            task_ignore_result=True,
        ),
    )

    db.init_app(app)
    cache.init_app(app)
    celery_init_app(app)
    CORS(app)

    # make sure upload folders exist
    static_dirs = [
        '../frontend/src/static/resumes',
        '../frontend/src/static/sent_reminders'
    ]
    for d in static_dirs:
        os.makedirs(os.path.abspath(os.path.join(os.path.dirname(__file__), d)), exist_ok=True)

    # load routes
    from backend.routes import register_routes
    register_routes(app)

    # create tables and mke admin
    with app.app_context():
        db.create_all()
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            hashed_pw = generate_password_hash('admin')
            new_admin = User(username='admin@admin.com', password=hashed_pw, role='admin', status='Approved')
            db.session.add(new_admin)
            db.session.commit()
            print("Database initialized and default Admin 'admin@admin.com' ('admin') created.")
        else:
            admin_user.username = 'admin@admin.com'
            admin_user.password = generate_password_hash('admin')
            db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)