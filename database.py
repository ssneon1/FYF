from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

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
    description = db.Column(db.Text, nullable=False)
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


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)  # reference to User.username
    date = db.Column(db.Date, default=datetime.utcnow().date, nullable=False)
    check_in_time = db.Column(db.DateTime)
    check_out_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Present')  # Present, Absent, Leave
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(20), nullable=False)  # weekly, monthly, daily
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    content_json = db.Column(db.Text)  # serialized summary payload
    recipients = db.Column(db.Text)  # comma-separated emails


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.String(80), nullable=False)  # manager/admin username
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.Date)