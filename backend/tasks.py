import os
import csv
from datetime import datetime
from celery import shared_task
from backend.models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application
from backend.email_service import send_email

# export studnt applications to csv
@shared_task
def export_student_applications(student_id):
    student = User.query.get(student_id)
    if not student:
        return f"Student {student_id} not found"
    
    apps = db.session.query(Application, PlacementDrive, CompanyProfile).join(
        PlacementDrive, Application.drive_id == PlacementDrive.id
    ).join(
        CompanyProfile, PlacementDrive.company_id == CompanyProfile.user_id
    ).filter(Application.student_id == student_id).all()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"student_{student_id}_applications_{timestamp}.csv"
    
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/src/static/exports'))
    os.makedirs(static_dir, exist_ok=True)
    filepath = os.path.join(static_dir, filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Student ID', 'Company Name', 'Drive Title', 'Application Status', 'Application Date'])
        for a, d, c in apps:
            writer.writerow([student_id, c.company_name, d.job_title, a.status, a.application_date])
            
    download_url = f"/frontend/src/static/exports/{filename}"
    notif_msg = f"Your applications export is ready. Download CSV at: {download_url}"
    send_email(student.username, "Data Export Ready", notif_msg)
    db.session.commit()
    
    return f"Export done for student {student_id}"

# send reminders to all eligble students for all open drives
@shared_task
def send_daily_reminders():
    drives = PlacementDrive.query.filter_by(status='Approved').all()
    students = User.query.filter_by(role='student', status='Approved').all()
    reminders_sent = 0

    for d in drives:
        for s in students:
            sp = StudentProfile.query.filter_by(user_id=s.id).first()
            if not sp:
                continue
            branch_match = (d.branch_criteria.lower() == 'all' or
                            d.branch_criteria.lower() in sp.branch.lower() or
                            sp.branch.lower() in d.branch_criteria.lower())
            cgpa_match = (sp.cgpa >= d.min_cgpa)
            if branch_match and cgpa_match:
                notif_msg = f"Reminder: {d.job_title} drive is open. Apply before {d.application_deadline}."
                send_email(s.username, f"Placement Drive Open: {d.job_title}", notif_msg)
                reminders_sent += 1

    db.session.commit()
    return f"Reminders sent: {reminders_sent}"
