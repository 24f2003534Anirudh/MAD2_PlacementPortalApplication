from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from datetime import datetime

# db and cache instances
db = SQLAlchemy()
cache = Cache()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False) # admin, company, or student
    status = db.Column(db.String(20), default='Approved') # Pending, Approved, or Blacklisted

class CompanyProfile(db.Model):
    __tablename__ = 'company_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    hr_contact = db.Column(db.String(50))
    website = db.Column(db.String(100))

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    resume = db.Column(db.String(100), default='')

class PlacementDrive(db.Model):
    __tablename__ = 'placement_drives'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    min_cgpa = db.Column(db.Float, nullable=False)
    branch_criteria = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, or Closed
    application_deadline = db.Column(db.String(20), default='')

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id'), nullable=False)
    application_date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Applied') # Applied, Shortlisted, Selected, or Rejected
    interview_date = db.Column(db.String(50), nullable=True)

class Placement(db.Model):
    __tablename__ = 'placements'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.String(50), default='N/A')
    joining_date = db.Column(db.String(50), default='')

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

