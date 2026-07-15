import os
import jwt
import datetime
from flask import request, jsonify, render_template, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models import db, cache, User, CompanyProfile, StudentProfile, PlacementDrive, Application, Notification, Placement
from backend.tasks import send_daily_reminders, export_student_applications
from backend.email_service import send_email
from datetime import datetime, timedelta

SECRET_KEY = 'super-secret-mvp-key'

def generate_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@cache.memoize(timeout=60)
def get_cached_approved_drives():
    drives = db.session.query(PlacementDrive, CompanyProfile).join(
        CompanyProfile, PlacementDrive.company_id == CompanyProfile.user_id
    ).filter(PlacementDrive.status == 'Approved').all()
    
    data = []
    for d, c in drives:
        data.append({
            'id': d.id,
            'company_id': d.company_id,
            'company_name': c.company_name,
            'job_title': d.job_title,
            'job_description': d.job_description,
            'min_cgpa': d.min_cgpa,
            'branch_criteria': d.branch_criteria,
            'application_deadline': d.application_deadline,
            'status': d.status
        })
    return data

def register_routes(app):
    
    # Entrypoint Template Server Route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Custom static route to serve frontend files correctly
    @app.route('/frontend/src/<path:filename>')
    def serve_frontend(filename):
        return send_from_directory(os.path.join(app.root_path, '../frontend/src'), filename)

    # AUTHENTICATION API ENDPOINTS
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        data = request.json
        if User.query.filter_by(username=data.get('username')).first():
            return jsonify({'message': 'Username already exists'}), 400
        
        hashed_pw = generate_password_hash(data.get('password'))
        role = data.get('role')
        
        # Companies start as Pending approval, students are auto-approved
        initial_status = 'Pending' if role == 'company' else 'Approved'
        
        new_user = User(username=data['username'], password=hashed_pw, role=role, status=initial_status)
        db.session.add(new_user)
        db.session.commit()
        
        if role == 'company':
            profile = CompanyProfile(user_id=new_user.id, company_name=data.get('company_name', data['username']), hr_contact=data.get('hr_contact'), website=data.get('website'))
            db.session.add(profile)
        elif role == 'student':
            profile = StudentProfile(user_id=new_user.id, cgpa=float(data.get('cgpa', 0)), branch=data.get('branch', 'General'), year=int(data.get('year', 2026)))
            db.session.add(profile)
            
        db.session.commit()
        return jsonify({'message': 'User registered successfully!'}), 201

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.json
        user = User.query.filter_by(username=data.get('username')).first()
        if not user or not check_password_hash(user.password, data.get('password')):
            return jsonify({'message': 'Invalid credentials'}), 401
        if user.status == 'Blacklisted':
            return jsonify({'message': 'Account deactivated or blacklisted.'}), 403
            
        token = generate_token(user.id, user.role)
        return jsonify({
            'token': token,
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'status': user.status
        }), 200

    # --- ADMIN ENDPOINTS ---
    @app.route('/api/admin/stats', methods=['GET'])
    def admin_stats():
        return jsonify({
            'total_students': User.query.filter_by(role='student').count(),
            'total_companies': User.query.filter_by(role='company').count(),
            'total_drives': PlacementDrive.query.count()
        }), 200

    @app.route('/api/admin/users', methods=['GET'])
    def get_users():
        q = request.args.get('q', '').strip().lower()
        users = User.query.filter(User.role != 'admin').all()
        user_list = []
        for u in users:
            details = {'id': u.id, 'user_id': u.id, 'username': u.username, 'role': u.role, 'status': u.status}
            company_name = ""
            if u.role == 'company':
                cp = CompanyProfile.query.filter_by(user_id=u.id).first()
                if cp: 
                    details['name'] = cp.company_name
                    details['hr_contact'] = cp.hr_contact
                    details['website'] = cp.website
                    company_name = cp.company_name
            else:
                sp = StudentProfile.query.filter_by(user_id=u.id).first()
                if sp: 
                    details['name'] = u.username
                    details['cgpa'] = sp.cgpa
                    details['branch'] = sp.branch
                    details['year'] = sp.year
                    details['resume'] = sp.resume
            
            # Apply search filter
            if q:
                match_username = q in u.username.lower()
                match_company = q in company_name.lower()
                match_role = q in u.role.lower()
                if not (match_username or match_company or match_role):
                    continue
                    
            user_list.append(details)
        return jsonify(user_list), 200

    @app.route('/api/admin/users/<int:user_id>/status', methods=['POST'])
    def update_user_status(user_id):
        user = User.query.get_or_404(user_id)
        user.status = request.json.get('status')
        db.session.commit()
        return jsonify({'message': f'Status updated to {user.status}'}), 200

    @app.route('/api/admin/drives', methods=['GET'])
    def admin_get_drives():
        drives = db.session.query(PlacementDrive, CompanyProfile).join(CompanyProfile, PlacementDrive.company_id == CompanyProfile.user_id).all()
        return jsonify([{
            'id': d.id,
            'company_name': c.company_name,
            'job_title': d.job_title,
            'min_cgpa': d.min_cgpa,
            'branch_criteria': d.branch_criteria,
            'application_deadline': d.application_deadline,
            'status': d.status
        } for d, c in drives]), 200

    @app.route('/api/admin/drives/<int:drive_id>/status', methods=['POST'])
    def update_drive_status(drive_id):
        drive = PlacementDrive.query.get_or_404(drive_id)
        drive.status = request.json.get('status')
        db.session.commit()
        # Invalidate approved drives cache
        cache.delete_memoized(get_cached_approved_drives)
        return jsonify({'message': f'Drive status updated to {drive.status}'}), 200

    @app.route('/api/admin/reminders/send', methods=['POST'])
    def trigger_reminders():
        send_daily_reminders.delay()
        return jsonify({'message': 'Reminders are being sent in the background!'}), 200

    # --- COMPANY ENDPOINTS ---
    @app.route('/api/company/drives', methods=['GET', 'POST'])
    def company_drives():
        company_id = request.args.get('company_id') or request.json.get('company_id') if request.json else None
        if request.method == 'POST':
            data = request.json
            user = User.query.get(data['company_id'])
            if user.status != 'Approved':
                return jsonify({'message': 'Company profile not approved by Admin yet.'}), 403
            
            new_drive = PlacementDrive(
                company_id=data['company_id'],
                job_title=data['job_title'],
                job_description=data['job_description'],
                min_cgpa=float(data['min_cgpa']),
                branch_criteria=data['branch_criteria'],
                application_deadline=data.get('application_deadline', ''),
                status='Pending'
            )
            db.session.add(new_drive)
            db.session.commit()
            return jsonify({'message': 'Drive created and awaiting admin approval.'}), 201
            
        drives = PlacementDrive.query.filter_by(company_id=company_id).all()
        drive_list = []
        for d in drives:
            app_count = Application.query.filter_by(drive_id=d.id).count()
            drive_list.append({
                'id': d.id, 'job_title': d.job_title, 'min_cgpa': d.min_cgpa,
                'branch_criteria': d.branch_criteria, 'application_deadline': d.application_deadline, 'status': d.status, 'applicants': app_count
            })
        return jsonify(drive_list), 200

    @app.route('/api/company/applications', methods=['GET'])
    def company_apps():
        company_id = request.args.get('company_id')
        apps = db.session.query(Application, User, PlacementDrive).join(User, Application.student_id == User.id).join(PlacementDrive, Application.drive_id == PlacementDrive.id).filter(PlacementDrive.company_id == company_id).all()
        
        result_list = []
        for a, u, d in apps:
            sp = StudentProfile.query.filter_by(user_id=u.id).first()
            result_list.append({
                'id': a.id,
                'student_name': u.username,
                'student_cgpa': sp.cgpa if sp else 0.0,
                'student_branch': sp.branch if sp else 'General',
                'job_title': d.job_title,
                'status': a.status,
                'interview_date': a.interview_date,
                'resume_url': sp.resume if sp else ''
            })
        return jsonify(result_list), 200

    @app.route('/api/company/applications/<int:app_id>/status', methods=['POST'])
    def update_app_status(app_id):
        app_rec = Application.query.get_or_404(app_id)
        new_status = request.json.get('status')
        app_rec.status = new_status
        
        if new_status == 'Selected':
            student = User.query.get(app_rec.student_id)
            drive = PlacementDrive.query.get(app_rec.drive_id)
            company = CompanyProfile.query.filter_by(user_id=drive.company_id).first()
            
            # Programmatic Placement record setup
            new_placement = Placement(
                student_id=app_rec.student_id,
                company_id=drive.company_id,
                position=drive.job_title,
                salary="12 LPA",
                joining_date="2026-08-01"
            )
            db.session.add(new_placement)
            
            subject = "You have been selected!"
            body = f"Congratulations! You have been selected by {company.company_name} for the position of {drive.job_title}."
            send_email(student.username, subject, body)
            
        elif new_status == 'Shortlisted':
            student = User.query.get(app_rec.student_id)
            drive = PlacementDrive.query.get(app_rec.drive_id)
            company = CompanyProfile.query.filter_by(user_id=drive.company_id).first()
            
            # Save interview date if provided
            interview_date = request.json.get('interview_date')
            if interview_date:
                app_rec.interview_date = interview_date
                notif_msg = f"You have been shortlisted by {company.company_name} for the position of {drive.job_title}! Interview scheduled for {interview_date}."
            else:
                notif_msg = f"You have been shortlisted by {company.company_name} for the position of {drive.job_title}!"
                
            subject = "Application Update: Shortlisted"
            send_email(student.username, subject, notif_msg)
            
        elif new_status == 'Rejected':
            student = User.query.get(app_rec.student_id)
            drive = PlacementDrive.query.get(app_rec.drive_id)
            company = CompanyProfile.query.filter_by(user_id=drive.company_id).first()
            subject = "Application Update: Rejected"
            body = f"Thank you for applying. {company.company_name} has updated your status for {drive.job_title} to Rejected."
            send_email(student.username, subject, body)
            
        db.session.commit()
        return jsonify({'message': 'Application status updated successfully.'}), 200

    # --- STUDENT ENDPOINTS ---
    @app.route('/api/student/drives', methods=['GET'])
    def student_get_drives():
        student_id = request.args.get('student_id')
        if not student_id:
            return jsonify({'message': 'student_id is required'}), 400
        student = StudentProfile.query.filter_by(user_id=student_id).first()
        if not student:
            return jsonify({'message': 'Student profile not found'}), 404
        
        drives_data = get_cached_approved_drives()
        
        result = []
        for d in drives_data:
            eligible = (student.cgpa >= d['min_cgpa']) and (d['branch_criteria'].lower() in ['all', student.branch.lower()])
            applied = Application.query.filter_by(student_id=student_id, drive_id=d['id']).first() is not None
            
            result.append({
                'id': d['id'], 'company_name': d['company_name'], 'job_title': d['job_title'],
                'job_description': d['job_description'], 'min_cgpa': d['min_cgpa'],
                'branch_criteria': d['branch_criteria'], 'application_deadline': d['application_deadline'],
                'eligible': eligible, 'applied': applied
            })
        return jsonify(result), 200

    @app.route('/api/student/profile', methods=['GET'])
    def get_student_profile():
        student_id = request.args.get('student_id')
        if not student_id:
            return jsonify({'message': 'student_id is required'}), 400
        sp = StudentProfile.query.filter_by(user_id=student_id).first()
        if not sp:
            return jsonify({'message': 'Student profile not found'}), 404
        return jsonify({
            'cgpa': sp.cgpa,
            'branch': sp.branch,
            'year': sp.year,
            'resume': sp.resume
        }), 200

    @app.route('/api/student/profile', methods=['POST'])
    def update_student_profile():
        student_id = request.form.get('student_id')
        if not student_id:
            return jsonify({'message': 'student_id is required'}), 400
            
        sp = StudentProfile.query.filter_by(user_id=student_id).first()
        if not sp:
            return jsonify({'message': 'Student profile not found'}), 404
            
        if 'cgpa' in request.form:
            sp.cgpa = float(request.form.get('cgpa'))
        if 'branch' in request.form:
            sp.branch = request.form.get('branch')
        if 'year' in request.form:
            sp.year = int(request.form.get('year'))
            
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename.endswith('.pdf'):
                filename = f"resume_student_{student_id}.pdf"
                static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/src/static/resumes'))
                filepath = os.path.join(static_dir, filename)
                file.save(filepath)
                sp.resume = f"/frontend/src/static/resumes/{filename}"
                
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully!', 'resume_url': sp.resume}), 200

    @app.route('/api/student/apply', methods=['POST'])
    def student_apply():
        data = request.json
        student_id = data['student_id']
        drive_id = data['drive_id']
        
        if Application.query.filter_by(student_id=student_id, drive_id=drive_id).first():
            return jsonify({'message': 'You have already applied to this drive.'}), 400
            
        student = StudentProfile.query.filter_by(user_id=student_id).first()
        drive = PlacementDrive.query.get(drive_id)
        
        if student.cgpa < drive.min_cgpa:
            return jsonify({'message': 'Application blocked: You do not meet the minimum CGPA requirement.'}), 400
            
        new_app = Application(
            student_id=student_id,
            drive_id=drive_id,
            application_date=datetime.now().strftime('%Y-%m-%d'),
            status='Applied'
        )
        db.session.add(new_app)
        db.session.commit()
        return jsonify({'message': 'Application submitted successfully.'}), 201

    @app.route('/api/student/history', methods=['GET'])
    def student_history():
        student_id = request.args.get('student_id')
        apps = db.session.query(Application, PlacementDrive, CompanyProfile).join(PlacementDrive, Application.drive_id == PlacementDrive.id).join(CompanyProfile, PlacementDrive.company_id == CompanyProfile.user_id).filter(Application.student_id == student_id).all()
        return jsonify([{
            'id': a.id,
            'company_name': c.company_name,
            'job_title': d.job_title,
            'date': a.application_date,
            'status': a.status,
            'interview_date': a.interview_date
        } for a, d, c in apps]), 200

    # Async Trigger Job Route
    @app.route('/api/student/export', methods=['POST'])
    def export_csv_job():
        student_id = request.json.get('student_id')
        if not student_id:
            return jsonify({'message': 'student_id is required'}), 400
        task = export_student_applications.delay(student_id)
        return jsonify({'message': 'CSV export job triggered in background!', 'task_id': task.id}), 202

    # --- SYSTEM NOTIFICATION ENDPOINTS ---
    @app.route('/api/notifications', methods=['GET'])
    def get_notifications():
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'message': 'user_id is required'}), 400
        notifs = Notification.query.filter_by(user_id=user_id).order_by(Notification.timestamp.desc()).all()
        return jsonify([{
            'id': n.id,
            'message': n.message,
            'timestamp': n.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': n.is_read
        } for n in notifs]), 200

    @app.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
    def mark_notification_read(notif_id):
        notif = Notification.query.get_or_404(notif_id)
        notif.is_read = True
        db.session.commit()
        return jsonify({'message': 'Notification marked as read'}), 200

    # --- CELERY MANUAL TRIGGERS FOR TESTING/EVALUATION ---
    @app.route('/api/test/daily-reminders', methods=['POST'])
    def trigger_daily_reminders():
        task = send_daily_reminders.delay()
        return jsonify({'message': 'Daily reminders task triggered in background!', 'task_id': task.id}), 202

    # --- SCHEDULER MANAGEMENT ---
    @app.route('/api/admin/schedules', methods=['GET'])
    def get_schedules():
        from backend.models import ReminderSchedule
        scheds = ReminderSchedule.query.all()
        return jsonify([{
            'id': s.id,
            'schedule_type': s.schedule_type,
            'run_at': s.run_at.strftime('%Y-%m-%d %H:%M:%S') if s.run_at else None,
            'interval_seconds': s.interval_seconds,
            'recurrence_hour': s.recurrence_hour,
            'recurrence_minute': s.recurrence_minute,
            'last_run': s.last_run.strftime('%Y-%m-%d %H:%M:%S') if s.last_run else None,
            'status': s.status
        } for s in scheds]), 200

    @app.route('/api/admin/schedules', methods=['POST'])
    def create_schedule():
        from backend.models import ReminderSchedule
        data = request.json
        stype = data.get('schedule_type')
        
        run_at = None
        if data.get('run_at'):
            try:
                run_at = datetime.strptime(data.get('run_at'), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    run_at = datetime.strptime(data.get('run_at'), '%Y-%m-%dT%H:%M')
                except ValueError:
                    run_at = None
                
        interval_seconds = data.get('interval_seconds')
        recurrence_hour = data.get('recurrence_hour')
        recurrence_minute = data.get('recurrence_minute')
        
        if interval_seconds is not None:
            interval_seconds = int(interval_seconds)
        if recurrence_hour is not None:
            recurrence_hour = int(recurrence_hour)
        if recurrence_minute is not None:
            recurrence_minute = int(recurrence_minute)
            
        sched = ReminderSchedule(
            schedule_type=stype,
            run_at=run_at,
            interval_seconds=interval_seconds,
            recurrence_hour=recurrence_hour,
            recurrence_minute=recurrence_minute
        )
        db.session.add(sched)
        db.session.commit()
        return jsonify({'message': 'Schedule created successfully!', 'id': sched.id}), 201

    @app.route('/api/admin/schedules/<int:sched_id>', methods=['DELETE'])
    def delete_schedule(sched_id):
        from backend.models import ReminderSchedule
        sched = ReminderSchedule.query.get_or_404(sched_id)
        db.session.delete(sched)
        db.session.commit()
        return jsonify({'message': 'Schedule deleted successfully!'}), 200