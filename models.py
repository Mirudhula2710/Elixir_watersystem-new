from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __bind_key__ = 'auth'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False) # manager, worker, student
    name = db.Column(db.String(64), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    telegram_chat_id = db.Column(db.String(64), nullable=True)
    preferred_language = db.Column(db.String(10), default='ta') # ta (Tamil), hi (Hindi), en (English)

class Zone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False)
    tank_level = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    expected_level = db.Column(db.Float, nullable=True)
    
    zone = db.relationship('Zone', backref=db.backref('readings', lazy=True))

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False)
    reading_id = db.Column(db.Integer, db.ForeignKey('reading.id'), nullable=False)
    severity = db.Column(db.String(50), nullable=False) # Normal, Warning, Suspected Leak, Critical
    deviation = db.Column(db.Float, nullable=False)
    gemini_explanation = db.Column(db.Text, nullable=True)
    gemini_explanation_ta = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='open') # open, assigned, resolved

    zone = db.relationship('Zone', backref=db.backref('alerts', lazy=True))
    reading = db.relationship('Reading')

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    linked_alert_id = db.Column(db.Integer, db.ForeignKey('alert.id'), nullable=True)
    status = db.Column(db.String(20), default='open') # open, in_progress, resolved

    
    zone = db.relationship('Zone')
    linked_alert = db.relationship('Alert')

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('alert.id'), nullable=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaint.id'), nullable=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False)
    assigned_worker_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='unassigned') # unassigned, assigned, in_progress, resolved
    worker_notes = db.Column(db.Text, nullable=True)

    alert = db.relationship('Alert', backref=db.backref('ticket', uselist=False))
    complaint = db.relationship('Complaint', backref=db.backref('ticket', uselist=False))
    zone = db.relationship('Zone')
    
