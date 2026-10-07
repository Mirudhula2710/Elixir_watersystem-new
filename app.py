from flask import Flask, render_template, redirect, url_for, request
from models import db
from auth import auth_bp
from flask_login import LoginManager, login_required, current_user
from auth import role_required
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # D17: Environment switch for DB_BACKEND
    db_backend = os.environ.get('DB_BACKEND', 'sqlite').lower()
    
    if db_backend == 'mysql':
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '3306')
        db_name = os.environ.get('DB_NAME', 'water_elixir')
        db_user = os.environ.get('DB_USERNAME', 'water_app_user')
        import urllib.parse
        raw_pass = os.environ.get('DB_PASSWORD', '')
        db_pass = urllib.parse.quote_plus(raw_pass)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    else:
        # Default SQLite mode with WAL and 30s busy timeout
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///water_app.db'
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'connect_args': {'timeout': 30}
        }
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # D12: Flask login users stay in auth SQLite
    app.config['SQLALCHEMY_BINDS'] = {
        'auth': 'sqlite:///users.db'
    }

    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    import sqlite3

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.close()

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from models import User, Zone, Alert, Complaint, Ticket, Reading

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'manager':
                return redirect(url_for('manager_dashboard'))
            elif current_user.role == 'worker':
                return redirect(url_for('worker_dashboard'))
            elif current_user.role == 'student':
                return redirect(url_for('student_dashboard'))
        return render_template('opening.html')

    @app.route('/manager')
    @login_required
    @role_required('manager')
    def manager_dashboard():
        zones = Zone.query.all()
        alerts = Alert.query.order_by(Alert.created_at.desc()).limit(10).all()
        complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(10).all()
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(10).all()
        workers = User.query.filter_by(role='worker').all()
        users_map = {u.id: u for u in User.query.all()}
        return render_template('manager.html', zones=zones, alerts=alerts, complaints=complaints, tickets=tickets, workers=workers, users=users_map)

    
    from notifications import notify_worker_via_telegram

    @app.route('/auto_assign', methods=['POST'])
    @login_required
    @role_required('manager')
    def auto_assign():
        unassigned_tickets = Ticket.query.filter_by(assigned_worker_id=None).order_by(Ticket.created_at.desc()).limit(10).all()
        workers = User.query.filter_by(role='worker').all()
        if workers and unassigned_tickets:
            import itertools
            import time
            worker_cycle = itertools.cycle(workers)
            for ticket in unassigned_tickets:
                worker = next(worker_cycle)
                ticket.assigned_worker_id = worker.id
                ticket.status = 'assigned'
                notify_worker_via_telegram(worker, ticket)
                time.sleep(0.3)
            db.session.commit()
        return redirect(url_for('manager_dashboard') + '#tab-tickets')


    @app.route('/update_ticket_status/<int:ticket_id>', methods=['POST'])
    @login_required
    @role_required('worker')
    def update_ticket_status(ticket_id):
        notes = request.form.get('notes')
        status = request.form.get('status')
        ticket = Ticket.query.get(ticket_id)
        if ticket and ticket.assigned_worker_id == current_user.id:
            ticket.status = status
            ticket.worker_notes = notes
            from datetime import datetime
            if status == 'RESOLVED' or status == 'resolved':
                ticket.resolved_at = datetime.utcnow()
                if ticket.complaint:
                    ticket.complaint.status = 'resolved'
            db.session.commit()
        return redirect(url_for('worker_dashboard'))

    @app.route('/worker', methods=['GET', 'POST'])

    @login_required
    @role_required('worker')
    def worker_dashboard():
        if request.method == 'POST':
            ticket_id = request.form.get('ticket_id')
            notes = request.form.get('notes')
            ticket = Ticket.query.get(ticket_id)
            if ticket and ticket.assigned_worker_id == current_user.id:
                ticket.status = 'resolved'
                ticket.worker_notes = notes
                ticket.resolved_at = datetime.utcnow()
                
                if ticket.alert:
                    ticket.alert.status = 'resolved'
                if ticket.complaint:
                    ticket.complaint.status = 'resolved'
                    
                # Reopen valve on resolution
                if ticket.zone:
                    ticket.zone.valve_state = 'OPEN'
                    
                db.session.commit()
                
        tickets = Ticket.query.filter_by(assigned_worker_id=current_user.id).all()
        return render_template('worker.html', tickets=tickets)

    @app.route('/student', methods=['GET', 'POST'])
    @login_required
    @role_required('student')
    def student_dashboard():
        allowed_blocks = ['SRM ARTS', 'SRM TRP', 'SRM IST', 'TWIN TOWER', 'BASIL RESTUARANT', 'AMBIS CAFE', 'SRM MEDICAL COLLEGE']
        for b_name in allowed_blocks:
            if not Zone.query.filter_by(name=b_name).first():
                db.session.add(Zone(name=b_name))
        db.session.commit()

        if request.method == 'POST':
            zone_id = request.form.get('zone_id')
            description = request.form.get('description')
            complaint = Complaint(student_id=current_user.id, zone_id=zone_id, description=description)
            db.session.add(complaint)
            db.session.flush()
            
            # Create unassigned ticket so manager can assign it to a worker
            ticket = Ticket(complaint_id=complaint.id, zone_id=zone_id, assigned_worker_id=None, status='unassigned')
            db.session.add(ticket)
            db.session.commit()
            
        complaints = Complaint.query.filter_by(student_id=current_user.id).order_by(Complaint.created_at.desc()).all()
        zones = Zone.query.filter(Zone.name.in_(allowed_blocks)).all()
        return render_template('student.html', complaints=complaints, zones=zones)

    @app.route('/auto_assign_complaint/<int:complaint_id>', methods=['POST'])
    @login_required
    @role_required('manager')
    def auto_assign_complaint(complaint_id):
        complaint = Complaint.query.get(complaint_id)
        workers = User.query.filter_by(role='worker').all()
        if complaint and workers:
            import random
            worker = random.choice(workers)
            ticket = Ticket.query.filter_by(complaint_id=complaint.id).first()
            if not ticket:
                ticket = Ticket(
                    complaint_id=complaint.id,
                    zone_id=complaint.zone_id,
                    assigned_worker_id=worker.id,
                    status='assigned'
                )
                db.session.add(ticket)
            else:
                ticket.assigned_worker_id = worker.id
                ticket.status = 'assigned'
                
            complaint.status = 'in_progress'
            db.session.commit()
            notify_worker_via_telegram(worker, ticket)
        return redirect(url_for('manager_dashboard') + '#tab-complaints')

    @app.route('/manual_assign_complaint/<int:complaint_id>', methods=['POST'])
    @login_required
    @role_required('manager')
    def manual_assign_complaint(complaint_id):
        worker_id = request.form.get('worker_id')
        complaint = Complaint.query.get(complaint_id)
        if complaint and worker_id and worker_id.strip():
            w_id = int(worker_id)
            worker = User.query.get(w_id)
            ticket = Ticket.query.filter_by(complaint_id=complaint.id).first()
            if not ticket:
                ticket = Ticket(
                    complaint_id=complaint.id,
                    zone_id=complaint.zone_id,
                    assigned_worker_id=w_id,
                    status='assigned'
                )
                db.session.add(ticket)
            else:
                ticket.assigned_worker_id = w_id
                ticket.status = 'assigned'
                
            complaint.status = 'in_progress'
            db.session.commit()
            if worker:
                notify_worker_via_telegram(worker, ticket)
        return redirect(url_for('manager_dashboard') + '#tab-complaints')

    @app.route('/assign_ticket/<int:ticket_id>', methods=['POST'])
    @login_required
    @role_required('manager')
    def assign_ticket(ticket_id):
        worker_id = request.form.get('worker_id')
        ticket = Ticket.query.get(ticket_id)
        if ticket:
            if worker_id and worker_id.strip():
                w_id = int(worker_id)
                worker = User.query.get(w_id)
                ticket.assigned_worker_id = w_id
                ticket.status = 'assigned'
                if ticket.complaint:
                    ticket.complaint.status = 'in_progress'
                db.session.commit()
                if worker:
                    notify_worker_via_telegram(worker, ticket)
            else:
                ticket.assigned_worker_id = None
                ticket.status = 'unassigned'
                if ticket.complaint:
                    ticket.complaint.status = 'open'
                db.session.commit()
        return redirect(url_for('manager_dashboard') + '#tab-tickets')

    return app

if __name__ == '__main__':
    app = create_app()
    # Ensure databases are created on first run
    with app.app_context():
        db.create_all()
        
    app.run(debug=True, port=5000, use_reloader=False)
