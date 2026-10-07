import socket
import json
import signal
import sys
import os
import time
import multiprocessing
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Zone, Reading, Alert, Ticket
from detection.physics_model import compute_expected_drainage
from detection.ml_model import predict_severity
from gemini.explain import explain_alert
from severity_map import to_backend_severity

HOST = '127.0.0.1'
PORT = 65432
ZONES = ['Hostel Blocks', 'Laboratories', 'Administration Building', 'Canteen']

def zone_worker(zone_name, queue):
    """
    Worker process for a specific zone.
    Reads from the queue, performs detection, and writes to the DB.
    """
    app = create_app()
    with app.app_context():
        print(f"[{zone_name}] Worker started.")
        while True:
            try:
                payload = queue.get()
                if payload is None:  # Sentinel value for shutdown
                    print(f"[{zone_name}] Shutting down worker.")
                    break
                
                tank_level = payload.get('level')
                if tank_level is None:
                    continue

                zone = Zone.query.filter_by(name=zone_name).first()
                if not zone:
                    print(f"[{zone_name}] Zone not found in DB!")
                    continue

                last_reading = Reading.query.filter_by(zone_id=zone.id).order_by(Reading.timestamp.desc()).first()
                
                expected_level = tank_level
                rate_of_change = 0.0
                dt = 0

                if last_reading:
                    dt = (datetime.utcnow() - last_reading.timestamp).total_seconds()
                    if dt > 0:
                        expected_level = compute_expected_drainage(last_reading.tank_level, dt)
                        rate_of_change = (tank_level - last_reading.tank_level) / dt
                
                # Save reading
                reading = Reading(zone_id=zone.id, tank_level=tank_level, expected_level=expected_level)
                db.session.add(reading)
                db.session.commit()

                # ML + Physics logic
                deviation = abs(tank_level - expected_level)
                now = datetime.now()
                feature_dict = {
                    "hour": now.hour,
                    "minute_of_day": now.hour * 60 + now.minute,
                    "tank_level": tank_level,
                    "expected_level": expected_level,
                    "rate_of_change": rate_of_change,
                    "zone_Administration Building": 1 if zone_name == "Administration Building" else 0,
                    "zone_Canteen": 1 if zone_name == "Canteen" else 0,
                    "zone_Hostel Blocks": 1 if zone_name == "Hostel Blocks" else 0,
                    "zone_Laboratories": 1 if zone_name == "Laboratories" else 0
                }

                severity_ml = predict_severity(feature_dict)
                
                # Physics severity mapping (per approved bands)
                deviation_pct = 0
                if expected_level > 0:
                    deviation_pct = (tank_level - expected_level) / expected_level * 100.0

                severity_phys = "Normal"
                if deviation_pct <= -20.0 or deviation_pct >= 28.0:
                    severity_phys = "Critical"
                elif deviation_pct < -10.0:
                    severity_phys = "Suspected Leak"
                elif deviation_pct < -4.25:
                    severity_phys = "Warning"

                # D11: Final severity is the HIGHER of physics and ML.
                severity_order = {"Normal": 0, "Warning": 1, "Suspected Leak": 2, "Critical": 3}
                val_ml = severity_order.get(severity_ml, 0)
                val_phys = severity_order.get(severity_phys, 0)
                
                final_severity = "Normal"
                trigger = "None"
                
                if val_phys >= val_ml and val_phys > 0:
                    final_severity = severity_phys
                    trigger = "Physics"
                elif val_ml > val_phys:
                    final_severity = severity_ml
                    trigger = "ML"
                
                print(f"[{zone_name}] Level: {tank_level:.2f} (Expected: {expected_level:.2f}) -> ML: {severity_ml}, Phys: {severity_phys}. Final: {final_severity} ({trigger})")

                if final_severity != "Normal":
                    alert = Alert(
                        zone_id=zone.id,
                        reading_id=reading.id,
                        severity=to_backend_severity(final_severity),
                        deviation=deviation
                    )
                    db.session.add(alert)
                    db.session.commit()
                    
                    try:
                        exp_en, exp_ta = explain_alert(zone_name, final_severity, deviation)
                        alert.gemini_explanation = exp_en
                        alert.gemini_explanation_ta = exp_ta
                    except Exception as e:
                        alert.gemini_explanation = f"Error generating explanation: {e}"
                        alert.gemini_explanation_ta = f"விளக்கம் உருவாக்கத்தில் பிழை: {e}"
                        
                    if final_severity == "Critical":
                        print(f"*** CRITICAL ALERT in {zone_name} *** Simulated Valve Shutoff executed.")
                        ticket = Ticket(
                            alert_id=alert.id,
                            zone_id=zone.id,
                            status='unassigned'
                        )
                        db.session.add(ticket)
                    
                    db.session.commit()

            except Exception as e:
                print(f"[{zone_name}] Worker error: {e}")

def main():
    queues = {}
    processes = {}
    
    for zone in ZONES:
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=zone_worker, args=(zone, q))
        p.start()
        queues[zone] = q
        processes[zone] = p

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def shutdown(sig, frame):
        print("\nShutting down central server...")
        for zone, q in queues.items():
            q.put(None)
        
        for zone, p in processes.items():
            p.join(timeout=3)
            if p.is_alive():
                print(f"[{zone}] Force terminating worker.")
                p.terminate()
        
        server_socket.close()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Central Server listening on {HOST}:{PORT}")
        
        while True:
            try:
                conn, addr = server_socket.accept()
                with conn:
                    data = conn.recv(1024)
                    if not data:
                        continue
                    try:
                        payload = json.loads(data.decode('utf-8'))
                        if 'zone' not in payload or 'level' not in payload:
                            print("Malformed JSON missing required fields.")
                            continue
                        
                        zone_name = payload['zone']
                        if zone_name in queues:
                            queues[zone_name].put(payload)
                        else:
                            print(f"Unknown zone: {zone_name}")
                    except json.JSONDecodeError:
                        print("Invalid JSON received.")
            except socket.error:
                break
    finally:
        server_socket.close()

if __name__ == '__main__':
    main()
