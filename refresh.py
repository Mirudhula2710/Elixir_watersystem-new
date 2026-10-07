from app import create_app
from models import db, Zone, Reading, Alert, Complaint, Ticket, User

PREDEFINED_ALERTS = [
    {
        "zone": "SRM IST",
        "severity": "Critical",
        "deviation": 14.5,
        "explanation": "Critical pressure drop detected in Main Overhead Tank. Torricelli physics model indicates severe line fracture. Immediate worker dispatch required.",
        "explanation_ta": "முக்கிய மேல்நிலை தொட்டியில் கடுமையான அழுத்த வீழ்ச்சி கண்டறியப்பட்டுள்ளது. குழாய் உடைப்பு ஏற்பட்டுள்ளது, உடனடியாக பணியாளர் தேவை."
    },
    {
        "zone": "TWIN TOWER",
        "severity": "Suspected Leak",
        "deviation": 9.2,
        "explanation": "Abnormal outflow rate of 9.2L/min detected during low-usage hours. AI SVM model flags high probability of underground pipe leak.",
        "explanation_ta": "குறைந்த பயன்பாட்டு நேரங்களில் 9.2L/நிமிடம் அசாதாரண நீர் வெளியேற்றம் கண்டறியப்பட்டது. நிலத்தடி குழாய் கசிவு இருக்க வாய்ப்புள்ளது."
    },
    {
        "zone": "BASIL RESTUARANT",
        "severity": "Warning",
        "deviation": 6.8,
        "explanation": "Slight flow rate imbalance detected in Kitchen Supply Line B. Recommended manual valve inspection.",
        "explanation_ta": "சமையலறை விநியோக வரிசை B இல் சிறிது ஓட்ட ஏற்றத்தாழ்வு கண்டறியப்பட்டது. கைமுறை வால்வு ஆய்வு பரிந்துரைக்கப்படுகிறது."
    },
    {
        "zone": "SRM TRP",
        "severity": "Suspected Leak",
        "deviation": 11.1,
        "explanation": "Continuous sensor level drop without active pump draw. Potential valve seal failure in Block 4 tank.",
        "explanation_ta": "தொடர்ச்சியான நீர் மட்ட வீழ்ச்சி கண்டறியப்பட்டது. பிளாக் 4 தொட்டியில் வால்வு முத்திரை செயலிழப்பு இருக்கலாம்."
    },
    {
        "zone": "AMBIS CAFE",
        "severity": "Warning",
        "deviation": 5.4,
        "explanation": "Minor pressure variance observed in ground floor supply lines. Non-critical, scheduled check advised.",
        "explanation_ta": "தரைத்தள விநியோகக் கோடுகளில் சிறிய அழுத்த வேறுபாடு காணப்பட்டது. திட்டமிடப்பட்ட சோதனை அறிவுறுத்தப்படுகிறது."
    },
    {
        "zone": "SRM MEDICAL COLLEGE",
        "severity": "Critical",
        "deviation": 16.8,
        "explanation": "Emergency: Main feeder pipe flow rate dropped by 16.8L. Automatic valve safety trigger initiated.",
        "explanation_ta": "அவசரநிலை: பிரதான தீடர் குழாய் ஓட்ட விகிதம் 16.8L குறைந்துள்ளது. தானியங்கி வால்வு பாதுகாப்பு தொடங்கப்பட்டது."
    },
    {
        "zone": "SRM ARTS",
        "severity": "Suspected Leak",
        "deviation": 8.0,
        "explanation": "Telemetry reading deviates by -8.0L from expected Torricelli curve. Inspection required near Arts Quadrangle.",
        "explanation_ta": "தொலைநிலை அளவீடு எதிர்பார்த்த அளவிலிருந்து -8.0L மாறுகிறது. கலைப் பகுதி அருகில் ஆய்வு தேவை."
    },
    {
        "zone": "SRM IST",
        "severity": "Warning",
        "deviation": 4.9,
        "explanation": "Low-level sensor jitter detected. Verify water meter calibration on Hostel Block C.",
        "explanation_ta": "சென்சார் அளவில் சிறிய மாறுபாடு கண்டறியப்பட்டது. விடுதி பிளாக் C இல் தண்ணீர் மீட்டரை சரிபார்க்கவும்."
    },
    {
        "zone": "TWIN TOWER",
        "severity": "Critical",
        "deviation": 13.2,
        "explanation": "Rapid water level drop in Tower B Secondary Reservoir. Immediate line closure & worker inspection required.",
        "explanation_ta": "டவர் B இரண்டாம் நிலை நீர்த்தேக்கத்தில் விரைவான நீர் மட்ட வீழ்ச்சி. உடனடியாக கோடு அடைப்பு மற்றும் ஆய்வு தேவை."
    },
    {
        "zone": "BASIL RESTUARANT",
        "severity": "Suspected Leak",
        "deviation": 7.5,
        "explanation": "Unusual night-time depletion detected. Inspection assigned for main intake manifold.",
        "explanation_ta": "இரவு நேரத்தில் அசாதாரண நீர் குறைவு கண்டறியப்பட்டது. பிரதான உட்கொள்ளும் பாதைக்கு ஆய்வு ஒதுக்கப்பட்டுள்ளது."
    }
]

def refresh_system():
    print("Resetting system state to 10 Unassigned Predefined Tasks for live presentation...")
    
    app = create_app()
    with app.app_context():
        try:
            # Clear old tickets, complaints, alerts, and readings
            db.session.query(Ticket).delete()
            db.session.query(Complaint).delete()
            db.session.query(Alert).delete()
            db.session.query(Reading).delete()
            db.session.commit()
            print("[SUCCESS] Cleared previous assignments, complaints, and alerts.")
        except Exception as e:
            db.session.rollback()
            print(f"[WARNING] Error clearing database: {e}")

        # Ensure all campus zones exist
        allowed_blocks = ['SRM ARTS', 'SRM TRP', 'SRM IST', 'TWIN TOWER', 'BASIL RESTUARANT', 'AMBIS CAFE', 'SRM MEDICAL COLLEGE']
        zone_map = {}
        for b_name in allowed_blocks:
            zone = Zone.query.filter_by(name=b_name).first()
            if not zone:
                zone = Zone(name=b_name)
                db.session.add(zone)
                db.session.flush()
            zone_map[b_name] = zone
        db.session.commit()

        # Seed the 10 predefined unassigned alerts & tickets
        for item in PREDEFINED_ALERTS:
            zone = zone_map.get(item['zone'])
            if zone:
                # Create dummy sensor reading
                reading = Reading(zone_id=zone.id, tank_level=75.0, expected_level=75.0 + item['deviation'])
                db.session.add(reading)
                db.session.flush()

                # Create Alert
                alert = Alert(
                    zone_id=zone.id,
                    reading_id=reading.id,
                    severity=item['severity'],
                    deviation=item['deviation'],
                    gemini_explanation=item['explanation'],
                    gemini_explanation_ta=item.get('explanation_ta', item['explanation']),
                    status='open'
                )
                db.session.add(alert)
                db.session.flush()

                # Create UNASSIGNED Ticket so it shows up in "Click here to assign works"
                ticket = Ticket(
                    alert_id=alert.id,
                    zone_id=zone.id,
                    assigned_worker_id=None,
                    status='unassigned'
                )
                db.session.add(ticket)

        # Preserve Worker Telegram & Phone settings for demo (all workers send alerts to your phone during demo)
        workers = User.query.filter_by(role='worker').all()
        for w in workers:
            w.phone_number = '+91 8122102645'
            w.telegram_chat_id = '7676329816'
            w.preferred_language = 'ta'

        db.session.commit()

    print("\n[SUCCESS] 10 Predefined Unassigned Alerts & Tickets generated!")
    print("-> All 10 tasks are now UNASSIGNED and visible under 'Click here to assign works to workers'.")
    print("-> You can now click 'Auto-Assign Works' or manually assign workers live in front of your professor!")

if __name__ == '__main__':
    refresh_system()
