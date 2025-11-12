from flask import Flask, render_template, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_socketio import SocketIO, emit, join_room

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
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Socket.IO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, manager, staff
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, default=0.0)
    fee = db.Column(db.Float, default=0.0)
    charge = db.Column(db.Float, default=0.0)
    link = db.Column(db.String(200))
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Received')  # Received, Pending, In Progress, Completed, Hold, Cancelled
    assigned_to = db.Column(db.String(100), nullable=False)
    branch_code = db.Column(db.String(50), nullable=False)
    paymode = db.Column(db.String(20), default='Cash')
    service_price = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    service_charge = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    edited = db.Column(db.Boolean, default=False)
    edit_reason = db.Column(db.Text)
    task_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # For task sharing - store as JSON string
    shared_with = db.Column(db.Text, default='[]')
    
    def get_shared_with(self):
        if not self.shared_with or self.shared_with.strip() == '':
            return []
        try:
            result = json.loads(self.shared_with)
            return result if isinstance(result, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_shared_with(self, staff_list):
        if not isinstance(staff_list, list):
            staff_list = []
        self.shared_with = json.dumps(staff_list)
    
    def is_completed(self):
        return self.status == 'Completed'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Real-time event handlers
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to real-time updates'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('join_room')
def handle_join_room(data):
    room = data.get('room', 'global')
    join_room(room)
    emit('room_joined', {'room': room, 'message': f'Joined room: {room}'})

# Function to broadcast task updates to all connected clients
def broadcast_task_update(event_type, task_data):
    socketio.emit('task_updated', {
        'type': event_type,
        'task': task_data,
        'timestamp': datetime.utcnow().isoformat()
    })

# Function to broadcast dashboard updates
def broadcast_dashboard_update():
    stats = get_dashboard_stats()
    socketio.emit('dashboard_updated', {
        'stats': stats,
        'timestamp': datetime.utcnow().isoformat()
    })

# Function to get dashboard stats (reusable)
def get_dashboard_stats():
    total_tasks = Task.query.count()
    today = datetime.now().date()
    tasks_today = Task.query.filter(Task.task_date == today).count()
    completed_tasks = Task.query.filter_by(status='Completed').count()
    total_revenue = db.session.query(db.func.sum(Task.paid_amount)).scalar() or 0
    overdue_threshold = datetime.now() - timedelta(hours=24)
    overdue_tasks = Task.query.filter(
        Task.status.in_(['Pending', 'In Progress', 'Hold']),
        Task.created_at < overdue_threshold
    ).count()

    return {
        'total_tasks': total_tasks,
        'tasks_today': tasks_today,
        'completed_tasks': completed_tasks,
        'total_revenue': total_revenue,
        'overdue_tasks': overdue_tasks
    }

def init_db():
    """Initialize the database with default data"""
    # Check if users already exist
    if not User.query.first():
        print("Initializing database with default data...")

        # Create default users
        users_data = [
            {'username': 'admin', 'role': 'admin', 'email': 'admin@taskflow.com'},
            {'username': 'manager', 'role': 'manager', 'email': 'manager@taskflow.com'},
            {'username': 'staff1', 'role': 'staff', 'email': 'staff1@taskflow.com'},
            {'username': 'staff2', 'role': 'staff', 'email': 'staff2@taskflow.com'},
            {'username': 'staff3', 'role': 'staff', 'email': 'staff3@taskflow.com'},
        ]

        for user_data in users_data:
            user = User(
                username=user_data['username'],
                role=user_data['role'],
                email=user_data['email']
            )
            if user_data['username'] == 'admin':
                user.set_password('admin123')
            elif user_data['username'] == 'manager':
                user.set_password('manager123')
            else:
                user.set_password('password123')
            db.session.add(user)

        # Create default services
        services_data = [
            {'name': 'Consultation', 'price': 1500, 'fee': 100, 'charge': 100,
             'link': 'https://example.com/consultation', 'note': 'Initial consultation for new clients'},
            {'name': 'Repair', 'price': 2000, 'fee': 150, 'charge': 150,
             'link': 'https://example.com/repair', 'note': 'Device repair service with 30-day warranty'},
            {'name': 'Sales', 'price': 500, 'fee': 50, 'charge': 50,
             'link': 'https://example.com/sales', 'note': 'Product sales and inquiry service'},
            {'name': 'Support', 'price': 800, 'fee': 80, 'charge': 80,
             'link': 'https://example.com/support', 'note': 'Technical support and troubleshooting'}
        ]

        for service_data in services_data:
            service = Service(**service_data)
            db.session.add(service)

        # Create sample tasks
        sample_tasks = [
            {
                'order_no': 'TF-001',
                'customer_name': 'Michael Brown',
                'contact_number': '555-1234',
                'service_type': 'Consultation',
                'status': 'Completed',
                'assigned_to': 'staff1',
                'branch_code': 'SHOP-A',
                'paymode': 'Credit Card',
                'service_price': 1500,
                'paid_amount': 1500,
                'service_charge': 100,
                'description': 'Initial business consultation',
                'task_date': datetime.now().date()
            },
            {
                'order_no': 'TF-002',
                'customer_name': 'Sarah Johnson',
                'contact_number': '555-5678',
                'service_type': 'Repair',
                'status': 'In Progress',
                'assigned_to': 'staff2',
                'branch_code': 'SHOP-B',
                'paymode': 'Cash',
                'service_price': 2000,
                'paid_amount': 1000,
                'service_charge': 150,
                'description': 'Device repair service',
                'task_date': datetime.now().date()
            }
        ]

        for task_data in sample_tasks:
            task = Task(**task_data)
            db.session.add(task)

        db.session.commit()
        print("Database initialized with default data")
    else:
        print("Database already contains data")

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
        try:
            last_number = int(last_task.order_no.split('-')[1])
            return f"TF-{last_number + 1:03d}"
        except (IndexError, ValueError):
            return "TF-001"
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
        # Broadcast service update
        socketio.emit('service_updated', {
            'type': 'created',
            'service': {
                'id': service.id,
                'name': service.name,
                'price': service.price,
                'fee': service.fee,
                'charge': service.charge,
                'link': service.link,
                'note': service.note
            }
        })
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
        # Broadcast service update
        socketio.emit('service_updated', {
            'type': 'updated',
            'service': {
                'id': service.id,
                'name': service.name,
                'price': service.price,
                'fee': service.fee,
                'charge': service.charge,
                'link': service.link,
                'note': service.note
            }
        })
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
        # Broadcast service update
        socketio.emit('service_updated', {
            'type': 'deleted',
            'service_id': service_id
        })
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
        description=data.get('description', ''),
        task_date=datetime.now().date()
    )

    try:
        db.session.add(task)
        db.session.commit()
        
        # Prepare task data for broadcasting
        task_data = {
            'id': task.id,
            'order_no': task.order_no,
            'customer_name': task.customer_name,
            'service_type': task.service_type,
            'status': task.status,
            'assigned_to': task.assigned_to,
            'branch_code': task.branch_code
        }
        
        # Broadcast task creation
        broadcast_task_update('created', task_data)
        # Broadcast dashboard update
        broadcast_dashboard_update()
        
        return jsonify({'success': True, 'message': 'Task created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create task'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()

    # Check if task is completed
    is_completed = task.is_completed()

    # Staff permissions
    if current_user.role == 'staff':
        # Check if staff is allowed to edit this task
        if task.assigned_to != current_user.username and current_user.username not in task.get_shared_with():
            return jsonify({'error': 'You can only edit tasks assigned to you or shared with you'}), 403
        
        # If task is completed, staff cannot edit anything
        if is_completed:
            return jsonify({'error': 'Cannot edit completed orders'}), 403
        
        # Staff can update these fields before completion
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
            
    # Manager permissions - full access
    elif current_user.role == 'manager':
        # Manager can update all fields at any time
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
        task.edit_reason = data.get('edit_reason', 'Manager edit')
    
    # Admin permissions - full access
    else:
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
        task.edit_reason = data.get('edit_reason', 'Admin edit')

    try:
        db.session.commit()
        
        # Prepare task data for broadcasting
        task_data = {
            'id': task.id,
            'order_no': task.order_no,
            'customer_name': task.customer_name,
            'service_type': task.service_type,
            'status': task.status,
            'assigned_to': task.assigned_to,
            'branch_code': task.branch_code
        }
        
        # Broadcast task update
        broadcast_task_update('updated', task_data)
        # Broadcast dashboard update
        broadcast_dashboard_update()
        
        return jsonify({'success': True, 'message': 'Task updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update task'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check if task is completed
    is_completed = task.is_completed()

    # Staff permissions
    if current_user.role == 'staff':
        # Check if staff is allowed to delete this task
        if task.assigned_to != current_user.username and current_user.username not in task.get_shared_with():
            return jsonify({'error': 'You can only delete tasks assigned to you or shared with you'}), 403
        
        # Staff cannot delete completed orders
        if is_completed:
            return jsonify({'error': 'Cannot delete completed orders'}), 403
        
        # Staff can only cancel (soft delete) orders that are not completed
        if data.get('status') != 'Cancelled':
            return jsonify({'error': 'Staff can only cancel orders by setting status to "Cancelled"'}), 403

    # Manager and Admin can delete any task
    elif current_user.role not in ['manager', 'admin']:
        return jsonify({'error': 'Access denied'}), 403

    try:
        # Store task data before deletion for broadcasting
        task_data = {
            'id': task.id,
            'order_no': task.order_no
        }
        
        db.session.delete(task)
        db.session.commit()
        
        # Broadcast task deletion
        broadcast_task_update('deleted', task_data)
        # Broadcast dashboard update
        broadcast_dashboard_update()
        
        return jsonify({'success': True, 'message': 'Task deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete task'}), 500

# Cancel task endpoint (soft delete for staff)
@app.route('/api/tasks/<int:task_id>/cancel', methods=['POST'])
@login_required
def cancel_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check if task is completed
    if task.is_completed() and current_user.role == 'staff':
        return jsonify({'error': 'Staff cannot cancel completed orders'}), 403
    
    # Check permissions
    if current_user.role == 'staff':
        if task.assigned_to != current_user.username and current_user.username not in task.get_shared_with():
            return jsonify({'error': 'You can only cancel tasks assigned to you or shared with you'}), 403

    # Update task status to cancelled
    task.status = 'Cancelled'
    task.edited = True
    task.edit_reason = f"Order cancelled by {current_user.username} ({current_user.role})"

    try:
        db.session.commit()
        
        # Broadcast task update
        task_data = {
            'id': task.id,
            'order_no': task.order_no,
            'status': task.status
        }
        broadcast_task_update('cancelled', task_data)
        broadcast_dashboard_update()
        
        return jsonify({'success': True, 'message': 'Task cancelled successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel task'}), 500

# Reopen completed task (Manager only)
@app.route('/api/tasks/<int:task_id>/reopen', methods=['POST'])
@login_required
def reopen_task(task_id):
    if current_user.role not in ['manager', 'admin']:
        return jsonify({'error': 'Only managers and admins can reopen completed orders'}), 403
    
    task = Task.query.get_or_404(task_id)
    
    if not task.is_completed():
        return jsonify({'error': 'Task is not completed'}), 400

    # Reopen the task by changing status to In Progress
    old_status = task.status
    task.status = 'In Progress'
    task.edited = True
    task.edit_reason = f"Order reopened from {old_status} by {current_user.username}"

    try:
        db.session.commit()
        
        # Broadcast task update
        task_data = {
            'id': task.id,
            'order_no': task.order_no,
            'status': task.status
        }
        broadcast_task_update('reopened', task_data)
        broadcast_dashboard_update()
        
        return jsonify({'success': True, 'message': 'Task reopened successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to reopen task'}), 500

# Take Over Task API
@app.route('/api/tasks/<int:task_id>/takeover', methods=['POST'])
@login_required
def take_over_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check if task is completed - staff cannot take over completed tasks
    if task.is_completed() and current_user.role == 'staff':
        return jsonify({'error': 'Cannot take over completed orders'}), 403
    
    # Check if task is already taken over by current user
    current_shared_with = task.get_shared_with()
    
    if current_user.username in current_shared_with:
        return jsonify({'error': 'You have already taken over this task'}), 400
    
    # Add current user to shared_with list
    current_shared_with.append(current_user.username)
    task.set_shared_with(current_shared_with)
    
    # Update edit reason
    task.edited = True
    task.edit_reason = f"Task taken over by {current_user.username}"
    
    try:
        db.session.commit()
        
        # Broadcast task update
        task_data = {
            'id': task.id,
            'order_no': task.order_no,
            'customer_name': task.customer_name,
            'service_type': task.service_type,
            'status': task.status,
            'assigned_to': task.assigned_to,
            'shared_with': task.get_shared_with()
        }
        broadcast_task_update('taken_over', task_data)
        
        return jsonify({
            'success': True, 
            'message': f'Task {task.order_no} taken over successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to take over task'}), 500

@app.route('/api/tasks/<int:task_id>/share', methods=['POST'])
@login_required
def share_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check if task is completed - staff cannot share completed tasks
    if task.is_completed() and current_user.role == 'staff':
        return jsonify({'error': 'Cannot share completed orders'}), 403
    
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
            
            # Broadcast task update for sharing
            task_data = {
                'id': task.id,
                'order_no': task.order_no,
                'shared_with': task.get_shared_with()
            }
            broadcast_task_update('shared', task_data)
            
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
        stats = get_dashboard_stats()
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

# Real-time refresh endpoint
@app.route('/api/refresh-data')
@login_required
def refresh_data():
    """Endpoint to manually trigger data refresh"""
    try:
        # Broadcast updates to all clients
        broadcast_dashboard_update()
        
        # Get latest tasks and broadcast
        tasks = Task.query.order_by(Task.created_at.desc()).limit(10).all()
        tasks_data = []
        for task in tasks:
            tasks_data.append({
                'id': task.id,
                'order_no': task.order_no,
                'customer_name': task.customer_name,
                'service_type': task.service_type,
                'status': task.status,
                'assigned_to': task.assigned_to
            })
        
        socketio.emit('tasks_refreshed', {'tasks': tasks_data})
        
        return jsonify({'success': True, 'message': 'Data refresh triggered'})
    except Exception as e:
        return jsonify({'error': 'Refresh failed'}), 500

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
    print("TaskFlow Application Started!")
    print("Default login credentials:")
    print("Admin: admin / admin123")
    print("Manager: manager / manager123") 
    print("Staff: staff1 / password123")
    print("Access the application at: http://localhost:5000")
    print("Real-time updates enabled via WebSocket")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
