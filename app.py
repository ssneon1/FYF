from flask import Flask, render_template, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from database import db, User, Service, Task
from models import init_db

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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Initialize database
with app.app_context():
    db.create_all()
    init_db()


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

    # Staff can update specific fields but need to provide reason for changes
    if current_user.role == 'staff':
        # Check if staff is allowed to edit this task
        if task.assigned_to != current_user.username and current_user.username not in task.get_shared_with():
            return jsonify({'error': 'You can only edit tasks assigned to you or shared with you'}), 403
        
        # Staff can update these fields
        allowed_fields = ['status', 'description', 'paid_amount', 'service_charge']
        
        # Track if any changes were made
        changes_made = False
        edit_reason_parts = []
        
        for field in allowed_fields:
            if field in data and getattr(task, field) != data[field]:
                old_value = getattr(task, field)
                new_value = data[field]
                setattr(task, field, new_value)
                changes_made = True
                edit_reason_parts.append(f"{field} changed from {old_value} to {new_value}")
        
        # If changes were made, mark as edited and record reason
        if changes_made:
            task.edited = True
            if data.get('edit_reason'):
                task.edit_reason = data.get('edit_reason')
            elif edit_reason_parts:
                task.edit_reason = "; ".join(edit_reason_parts)
        else:
            return jsonify({'error': 'No allowed fields were modified'}), 400
            
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
