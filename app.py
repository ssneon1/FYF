from flask import Flask, render_template, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from database import db, User, Service, Task, Attendance, Report, Announcement
from models import init_db
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import send_file
import io
import csv

app = Flask(__name__)

# Load environment variables (optional)
load_dotenv()

# Use a stable on-disk SQLite path by default (portable across machines)
basedir = os.path.abspath(os.path.dirname(__file__))
default_db_path = os.path.join(basedir, 'taskflow.db')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'taskflow-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f"sqlite:///{default_db_path}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'no-reply@fyf-crm.local')
ADMIN_EMAILS = [e.strip() for e in os.getenv('ADMIN_EMAILS', 'admin@fyf.local').split(',')]


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Initialize database
with app.app_context():
    db.create_all()
    init_db()

    # Initialize scheduler after DB init
    scheduler = BackgroundScheduler()

    # Jobs: weekly/monthly reports, overdue alerts, daily reminders
    scheduler.add_job(func=lambda: send_weekly_report(), trigger='cron', day_of_week='mon', hour=8, minute=0, id='weekly_report')
    scheduler.add_job(func=lambda: send_monthly_report(), trigger='cron', day=1, hour=8, minute=0, id='monthly_report')
    scheduler.add_job(func=lambda: send_overdue_alerts(), trigger='cron', hour=9, minute=0, id='overdue_alerts_daily')
    scheduler.add_job(func=lambda: send_daily_reminders(), trigger='cron', hour=10, minute=0, id='daily_reminders')
    try:
        scheduler.start()
    except Exception as e:
        print(f"Scheduler start failed: {e}")


# Utility functions
def get_staff_list():
    return [user.username for user in User.query.filter_by(role='staff').all()]


def generate_order_no():
    last_task = Task.query.order_by(Task.id.desc()).first()
    if last_task:
        last_number = int(last_task.order_no.split('-')[1])
        return f"TF-{last_number + 1:03d}"
    else:
        return "TF-001"


# Email utility
def send_email(to_addresses, subject, body):
    if not isinstance(to_addresses, list):
        to_addresses = [to_addresses]
    if not SMTP_SERVER or not SMTP_USER or not SMTP_PASSWORD:
        # Fallback: print to console for development
        print(f"[EMAIL MOCK] To: {to_addresses}\nSubject: {subject}\n{body}")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = ', '.join(to_addresses)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, to_addresses, msg.as_string())
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False


# Scheduled report and notification jobs
def build_summary(period_days=7):
    end = datetime.now().date()
    start = end - timedelta(days=period_days)
    total_tasks = Task.query.filter(Task.task_date.between(start, end)).count()
    completed = Task.query.filter(Task.task_date.between(start, end), Task.status == 'Completed').count()
    revenue = db.session.query(db.func.sum(Task.paid_amount)).filter(Task.task_date.between(start, end)).scalar() or 0
    return {
        'start': start.isoformat(),
        'end': end.isoformat(),
        'total_tasks': total_tasks,
        'completed_tasks': completed,
        'total_revenue': revenue
    }


def send_weekly_report():
    summary = build_summary(7)
    subject = "FYF Weekly Report"
    body = f"""
    <h3>Weekly Report ({summary['start']} to {summary['end']})</h3>
    <ul>
      <li>Total tasks: {summary['total_tasks']}</li>
      <li>Completed tasks: {summary['completed_tasks']}</li>
      <li>Total revenue: ₹{summary['total_revenue']}</li>
    </ul>
    """
    send_email(ADMIN_EMAILS, subject, body)
    # Persist report
    report = Report(report_type='weekly', period_start=datetime.fromisoformat(summary['start']).date(), period_end=datetime.fromisoformat(summary['end']).date(), content_json=json.dumps(summary), recipients=','.join(ADMIN_EMAILS))
    db.session.add(report)
    db.session.commit()


def send_monthly_report():
    summary = build_summary(30)
    subject = "FYF Monthly Report"
    body = f"""
    <h3>Monthly Report ({summary['start']} to {summary['end']})</h3>
    <ul>
      <li>Total tasks: {summary['total_tasks']}</li>
      <li>Completed tasks: {summary['completed_tasks']}</li>
      <li>Total revenue: ₹{summary['total_revenue']}</li>
    </ul>
    """
    send_email(ADMIN_EMAILS, subject, body)
    report = Report(report_type='monthly', period_start=datetime.fromisoformat(summary['start']).date(), period_end=datetime.fromisoformat(summary['end']).date(), content_json=json.dumps(summary), recipients=','.join(ADMIN_EMAILS))
    db.session.add(report)
    db.session.commit()


def send_overdue_alerts():
    overdue_threshold = datetime.now() - timedelta(hours=24)
    overdue = Task.query.filter(Task.status.in_(['Pending', 'In Progress', 'Hold']), Task.created_at < overdue_threshold).all()
    if not overdue:
        return
    grouped = {}
    for t in overdue:
        grouped.setdefault(t.assigned_to, []).append(t)
    for staff, items in grouped.items():
        body = "<h4>Overdue tasks alert</h4><ul>" + ''.join([f"<li>{i.order_no} - {i.customer_name} ({i.service_type})</li>" for i in items]) + "</ul>"
        # Send to admin and staff if email known (mock: staff@fyf.local)
        recipients = ADMIN_EMAILS + [f"{staff}@fyf.local"]
        send_email(recipients, "Overdue Tasks Alert", body)


def send_daily_reminders():
    today = datetime.now().date()
    staff_users = User.query.filter_by(role='staff').all()
    for staff in staff_users:
        tasks_today = Task.query.filter_by(assigned_to=staff.username, task_date=today).all()
        body = f"<h4>Daily Tasks for {staff.username}</h4><ul>" + ''.join([f"<li>{t.order_no} - {t.service_type} ({t.status})</li>" for t in tasks_today]) + "</ul>"
        send_email([f"{staff.username}@fyf.local"], "Daily Task Reminder", body)


# --- Attendance APIs ---
@app.route('/api/attendance/checkin', methods=['POST'])
@login_required
def attendance_checkin():
    entry = Attendance(user_id=current_user.id, checkin_time=datetime.now(), status='present')
    db.session.add(entry)
    db.session.commit()
    return jsonify({'message': 'Checked in', 'checkin_time': entry.checkin_time.isoformat()})


@app.route('/api/attendance/checkout', methods=['POST'])
@login_required
def attendance_checkout():
    today = datetime.now().date()
    entry = Attendance.query.filter_by(user_id=current_user.id).filter(db.func.date(Attendance.checkin_time) == today).order_by(Attendance.checkin_time.desc()).first()
    if not entry:
        return jsonify({'error': 'No check-in found'}), 400
    entry.checkout_time = datetime.now()
    db.session.commit()
    return jsonify({'message': 'Checked out', 'checkout_time': entry.checkout_time.isoformat()})


@app.route('/api/attendance/list', methods=['GET'])
@login_required
def attendance_list():
    user_id = request.args.get('user_id')
    q = Attendance.query
    if user_id:
        q = q.filter_by(user_id=int(user_id))
    records = [
        {
            'id': r.id,
            'user_id': r.user_id,
            'checkin_time': r.checkin_time.isoformat() if r.checkin_time else None,
            'checkout_time': r.checkout_time.isoformat() if r.checkout_time else None,
            'status': r.status
        } for r in q.order_by(Attendance.checkin_time.desc()).limit(200).all()
    ]
    return jsonify(records)


# --- Announcements APIs ---
@app.route('/api/announcements', methods=['GET'])
@login_required
def list_announcements():
    now = datetime.now()
    anns = Announcement.query.filter((Announcement.expires_at.is_(None)) | (Announcement.expires_at > now)).order_by(Announcement.created_at.desc()).all()
    return jsonify([
        {
            'id': a.id,
            'title': a.title,
            'message': a.message,
            'audience': a.audience,
            'created_at': a.created_at.isoformat(),
            'expires_at': a.expires_at.isoformat() if a.expires_at else None
        } for a in anns
    ])


@app.route('/api/announcements', methods=['POST'])
@login_required
def create_announcement():
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Not authorized'}), 403
    data = request.get_json()
    expires_at = None
    if data.get('expires_at'):
        try:
            expires_at = datetime.fromisoformat(data['expires_at'])
        except Exception:
            pass
    ann = Announcement(title=data.get('title', ''), message=data.get('message', ''), audience=data.get('audience', 'all'), created_by=current_user.id, expires_at=expires_at)
    db.session.add(ann)
    db.session.commit()
    return jsonify({'message': 'Announcement created', 'id': ann.id})


# --- Export API (CSV) ---
@app.route('/api/export/tasks.csv', methods=['GET'])
@login_required
def export_tasks_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['order_no', 'service_type', 'customer_name', 'assigned_to', 'status', 'task_date', 'paid_amount'])
    for t in Task.query.order_by(Task.created_at.desc()).limit(500).all():
        writer.writerow([t.order_no, t.service_type, t.customer_name, t.assigned_to, t.status, t.task_date.isoformat() if t.task_date else '', t.paid_amount])
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='tasks.csv')


# --- Auto-assign API ---
@app.route('/api/tasks/auto-assign', methods=['POST'])
@login_required
def auto_assign_tasks():
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Not authorized'}), 403
    data = request.get_json() or {}
    service_type = data.get('service_type')
    pending_tasks = Task.query.filter_by(status='Pending')
    if service_type:
        pending_tasks = pending_tasks.filter_by(service_type=service_type)
    pending_tasks = pending_tasks.order_by(Task.created_at.asc()).limit(50).all()

    staff_users = User.query.filter_by(role='staff').all()
    if not staff_users:
        return jsonify({'error': 'No staff users available'}), 400

    # Build workload map: count of active tasks per staff
    active_status = ['Pending', 'In Progress', 'Hold']
    workload = {u.username: Task.query.filter_by(assigned_to=u.username).filter(Task.status.in_(active_status)).count() for u in staff_users}
    staff_sorted = sorted(staff_users, key=lambda u: workload[u.username])

    assigned = []
    i = 0
    for t in pending_tasks:
        staff = staff_sorted[i % len(staff_sorted)]
        t.assigned_to = staff.username
        t.status = 'In Progress'
        assigned.append({'order_no': t.order_no, 'assigned_to': t.assigned_to})
        i += 1
    db.session.commit()
    return jsonify({'assigned': assigned, 'count': len(assigned)})


# Authentication routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        login_user(user)
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'email': user.email
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid credentials'
        }), 401


@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True, 'message': 'Logout successful'})


@app.route('/api/current-user')
@login_required
def current_user_info():
    return jsonify({
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'role': current_user.role,
            'email': current_user.email
        }
    })


# User management routes
@app.route('/api/users')
@login_required
def get_users():
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Access denied'}), 403

    users = User.query.all()
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'email': user.email,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })

    return jsonify(users_data)


@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    email = data.get('email')

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = User(username=username, role=role, email=email)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'User created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user'}), 500


# Service management routes
@app.route('/api/services')
@login_required
def get_services():
    try:
        services = Service.query.all()
        services_data = []
        for service in services:
            services_data.append({
                'id': service.id,
                'name': service.name,
                'price': service.price,
                'fee': service.fee,
                'charge': service.charge,
                'link': service.link,
                'note': service.note,
                'created_at': service.created_at.isoformat() if service.created_at else None
            })

        return jsonify(services_data)
    except Exception as e:
        return jsonify({'error': 'Database error'}), 500


@app.route('/api/services', methods=['POST'])
@login_required
def create_service():
    if current_user.role == 'staff':
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    service = Service(
        name=data.get('name'),
        price=data.get('price', 0),
        fee=data.get('fee', 0),
        charge=data.get('charge', 0),
        link=data.get('link', ''),
        note=data.get('note', '')
    )

    try:
        db.session.add(service)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Service created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create service'}), 500


@app.route('/api/services/<int:service_id>', methods=['PUT'])
@login_required
def update_service(service_id):
    if current_user.role == 'staff':
        return jsonify({'error': 'Access denied'}), 403

    service = Service.query.get_or_404(service_id)
    data = request.get_json()

    service.name = data.get('name', service.name)
    service.price = data.get('price', service.price)
    service.fee = data.get('fee', service.fee)
    service.charge = data.get('charge', service.charge)
    service.link = data.get('link', service.link)
    service.note = data.get('note', service.note)

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Service updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update service'}), 500


@app.route('/api/services/<int:service_id>', methods=['DELETE'])
@login_required
def delete_service(service_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    service = Service.query.get_or_404(service_id)

    try:
        db.session.delete(service)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Service deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete service'}), 500


# Task management routes
@app.route('/api/tasks')
@login_required
def get_tasks():
    try:
        # Get filter parameters
        date_filter = request.args.get('date', 'all')
        branch_filter = request.args.get('branch', 'all')
        staff_filter = request.args.get('staff', 'all')
        status_filter = request.args.get('status', 'all')
        service_filter = request.args.get('service', 'all')
        search_term = request.args.get('search', '')

        # Start with base query
        query = Task.query

        # Apply filters
        if date_filter != 'all':
            today = datetime.now().date()
            if date_filter == 'today':
                query = query.filter(Task.task_date == today)
            elif date_filter == 'yesterday':
                query = query.filter(Task.task_date == today - timedelta(days=1))
            elif date_filter == 'tomorrow':
                query = query.filter(Task.task_date == today + timedelta(days=1))
            elif date_filter == 'last30':
                query = query.filter(Task.task_date >= today - timedelta(days=30))

        if branch_filter != 'all':
            query = query.filter(Task.branch_code == branch_filter)

        if staff_filter != 'all':
            query = query.filter(Task.assigned_to == staff_filter)

        if status_filter != 'all':
            query = query.filter(Task.status == status_filter)

        if service_filter != 'all':
            query = query.filter(Task.service_type == service_filter)

        if search_term:
            query = query.filter(
                (Task.order_no.ilike(f'%{search_term}%')) |
                (Task.customer_name.ilike(f'%{search_term}%')) |
                (Task.contact_number.ilike(f'%{search_term}%'))
            )

        # For staff users, only show assigned tasks and shared tasks
        if current_user.role == 'staff':
            query = query.filter(
                (Task.assigned_to == current_user.username) |
                (Task.shared_with.contains(f'"{current_user.username}"'))
            )

        tasks = query.order_by(Task.created_at.desc()).all()

        tasks_data = []
        for task in tasks:
            tasks_data.append({
                'id': task.id,
                'order_no': task.order_no,
                'customer_name': task.customer_name,
                'contact_number': task.contact_number,
                'service_type': task.service_type,
                'status': task.status,
                'assigned_to': task.assigned_to,
                'branch_code': task.branch_code,
                'paymode': task.paymode,
                'service_price': task.service_price,
                'paid_amount': task.paid_amount,
                'service_charge': task.service_charge,
                'description': task.description,
                'edited': task.edited,
                'edit_reason': task.edit_reason,
                'shared_with': task.get_shared_with(),
                'task_date': task.task_date.isoformat() if task.task_date else None,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'updated_at': task.updated_at.isoformat() if task.updated_at else None
            })

        return jsonify(tasks_data)
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return jsonify({'error': 'Database error'}), 500


@app.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()

    task = Task(
        order_no=generate_order_no(),
        customer_name=data.get('customer_name'),
        contact_number=data.get('contact_number'),
        service_type=data.get('service_type'),
        assigned_to=data.get('assigned_to'),
        branch_code=data.get('branch_code'),
        paymode=data.get('paymode', 'Cash'),
        service_price=data.get('service_price', 0),
        paid_amount=data.get('paid_amount', 0),
        service_charge=data.get('service_charge', 0),
        description=data.get('description'),
        task_date=datetime.now().date()
    )

    try:
        db.session.add(task)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create task'}), 500


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()

    # Staff can only update status and need to provide reason for other changes
    if current_user.role == 'staff':
        new_status = data.get('status')
        if new_status and new_status != task.status:
            task.status = new_status
            task.edited = True
            task.edit_reason = f"Status changed from {task.status} to {new_status}"
        else:
            return jsonify({'error': 'Staff can only update task status'}), 403
    else:
        # Admin/Manager can update all fields
        task.customer_name = data.get('customer_name', task.customer_name)
        task.contact_number = data.get('contact_number', task.contact_number)
        task.service_type = data.get('service_type', task.service_type)
        task.assigned_to = data.get('assigned_to', task.assigned_to)
        task.branch_code = data.get('branch_code', task.branch_code)
        task.paymode = data.get('paymode', task.paymode)
        task.service_price = data.get('service_price', task.service_price)
        task.paid_amount = data.get('paid_amount', task.paid_amount)
        task.service_charge = data.get('service_charge', task.service_charge)
        task.description = data.get('description', task.description)
        task.status = data.get('status', task.status)
        task.edited = True
        task.edit_reason = data.get('edit_reason', '')

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update task'}), 500


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    task = Task.query.get_or_404(task_id)

    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete task'}), 500


@app.route('/api/tasks/<int:task_id>/share', methods=['POST'])
@login_required
def share_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    staff_to_share = data.get('staff_name')

    if not staff_to_share:
        return jsonify({'error': 'Staff name is required'}), 400

    shared_with = task.get_shared_with()
    if not isinstance(shared_with, list):
        shared_with = []
    
    if staff_to_share not in shared_with:
        shared_with.append(staff_to_share)
        task.set_shared_with(shared_with)

        try:
            db.session.commit()
            return jsonify({'success': True, 'message': f'Task shared with {staff_to_share}'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to share task'}), 500

    return jsonify({'success': True, 'message': 'Task already shared with this staff'})


# Dashboard data routes
@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    try:
        total_tasks = Task.query.count()

        today = datetime.now().date()
        tasks_today = Task.query.filter(Task.task_date == today).count()

        completed_tasks = Task.query.filter_by(status='Completed').count()

        total_revenue = db.session.query(db.func.sum(Task.paid_amount)).scalar() or 0

        # Overdue tasks (Pending/In Progress/Hold for more than 24 hours)
        overdue_threshold = datetime.now() - timedelta(hours=24)
        overdue_tasks = Task.query.filter(
            Task.status.in_(['Pending', 'In Progress', 'Hold']),
            Task.created_at < overdue_threshold
        ).count()

        stats = {
            'total_tasks': total_tasks,
            'tasks_today': tasks_today,
            'completed_tasks': completed_tasks,
            'total_revenue': total_revenue,
            'overdue_tasks': overdue_tasks
        }

        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': 'Database error'}), 500


@app.route('/api/dashboard/top-performers')
@login_required
def top_performers():
    try:
        # Get staff performance data
        staff_performance = []
        staff_users = User.query.filter_by(role='staff').all()

        for staff in staff_users:
            staff_tasks = Task.query.filter_by(assigned_to=staff.username).all()
            completed_tasks = len([t for t in staff_tasks if t.status == 'Completed'])
            total_revenue = sum(task.paid_amount for task in staff_tasks)
            score = completed_tasks * 10 + total_revenue / 100

            staff_performance.append({
                'name': staff.username,
                'completed_tasks': completed_tasks,
                'total_revenue': total_revenue,
                'score': score
            })

        # Sort by score and get top 3
        staff_performance.sort(key=lambda x: x['score'], reverse=True)
        top_performers = staff_performance[:3]

        return jsonify(top_performers)
    except Exception as e:
        return jsonify({'error': 'Database error'}), 500


@app.route('/api/dashboard/overdue-tasks')
@login_required
def overdue_tasks():
    try:
        overdue_threshold = datetime.now() - timedelta(hours=24)
        overdue_tasks = Task.query.filter(
            Task.status.in_(['Pending', 'In Progress', 'Hold']),
            Task.created_at < overdue_threshold
        ).all()

        tasks_data = []
        for task in overdue_tasks:
            hours_overdue = int((datetime.now() - task.created_at).total_seconds() / 3600)
            tasks_data.append({
                'order_no': task.order_no,
                'customer_name': task.customer_name,
                'service_type': task.service_type,
                'status': task.status,
                'assigned_to': task.assigned_to,
                'task_date': task.task_date.isoformat() if task.task_date else None,
                'hours_overdue': hours_overdue
            })

        return jsonify(tasks_data)
    except Exception as e:
        return jsonify({'error': 'Database error'}), 500


# Main route
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health')
def health_check():
    try:
        # Test database connection
        User.query.first()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)