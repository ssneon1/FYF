from database import db, User, Service, Task
from datetime import datetime


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
            {'username': 'staff4', 'role': 'staff', 'email': 'staff4@taskflow.com'},
            {'username': 'staff5', 'role': 'staff', 'email': 'staff5@taskflow.com'},
            {'username': 'staff6', 'role': 'staff', 'email': 'staff6@taskflow.com'},
            {'username': 'staff7', 'role': 'staff', 'email': 'staff7@taskflow.com'},
            {'username': 'staff8', 'role': 'staff', 'email': 'staff8@taskflow.com'},
        ]

        for user_data in users_data:
            user = User(
                username=user_data['username'],
                role=user_data['role'],
                email=user_data['email']
            )
            if user_data['username'] == 'admin':
                user.set_password('admin123')
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