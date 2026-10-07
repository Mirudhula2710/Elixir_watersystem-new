from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Make sure tables exist
    db.create_all()

    users_to_add = [
        {"username": "manager", "role": "manager", "name": "Manager"},
        {"username": "worker1", "role": "worker", "name": "Worker 1", "phone_number": "+91 8122102645"},
        {"username": "worker2", "role": "worker", "name": "Worker 2"},
        {"username": "worker3", "role": "worker", "name": "Worker 3"},
        {"username": "student", "role": "student", "name": "Student 1"},
    ]

    for user_data in users_to_add:
        user = User.query.filter_by(username=user_data['username']).first()
        if not user:
            print(f"Creating user: {user_data['username']}")
            new_user = User(
                username=user_data['username'],
                password_hash=generate_password_hash("password"),
                role=user_data['role'],
                name=user_data['name'],
                phone_number=user_data.get('phone_number')
            )
            db.session.add(new_user)
        else:
            print(f"User {user_data['username']} already exists. Updating details.")
            user.password_hash = generate_password_hash("password")
            if user_data.get('phone_number'):
                user.phone_number = user_data['phone_number']
            
    db.session.commit()
    print("All demo users seeded successfully in users.db!")
