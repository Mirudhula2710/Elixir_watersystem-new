from app import create_app
from models import db, User, Zone, Reading, Alert, Complaint, Ticket
from werkzeug.security import generate_password_hash

def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Seed Zones
        zones = ['SRM ARTS', 'SRM TRP', 'SRM IST', 'TWIN TOWER', 'BASIL RESTUARANT', 'AMBIS CAFE', 'SRM MEDICAL COLLEGE']
        for z_name in zones:
            if not Zone.query.filter_by(name=z_name).first():
                db.session.add(Zone(name=z_name))

        # Seed Manager
        if not User.query.filter_by(username='manager').first():
            db.session.add(User(
                username='manager',
                password_hash=generate_password_hash('password'),
                role='manager',
                name='Alice Manager'
            ))

        # Seed Workers
        for i in range(1, 4):
            uname = f'worker{i}'
            if not User.query.filter_by(username=uname).first():
                db.session.add(User(
                    username=uname,
                    password_hash=generate_password_hash('password'),
                    role='worker',
                    name=f'Bob Worker {i}'
                ))

        # Seed Students
        for i in range(1, 4):
            uname = f'student{i}'
            if not User.query.filter_by(username=uname).first():
                db.session.add(User(
                    username=uname,
                    password_hash=generate_password_hash('password'),
                    role='student',
                    name=f'Charlie Student {i}'
                ))

        db.session.commit()
        print("Database seeded successfully.")

if __name__ == '__main__':
    seed()
