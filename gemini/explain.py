import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def explain_alert(zone_name, severity, deviation):
    api_key = os.getenv("GEMINI_API_KEY")
    
    explanation_en = ""
    explanation_ta = ""

    if severity == "Critical":
        explanation_en = f"A critical deviation of {deviation:.2f} liters indicates abnormal, high-volume water loss in the {zone_name} that strongly points to an active pipe rupture, failed fixture, or stuck open valve. Immediately dispatch a technician to inspect supply lines and equipment, and isolate the local zone shutoff valve if uncontrolled flow or pooling water is detected."
        explanation_ta = f"{zone_name} இல் {deviation:.2f} லிட்டர் நீர் இழப்பு கண்டறியப்பட்டுள்ளது. இது பிரதான குழாய் உடைப்பு அல்லது வால்வு செயலிழப்பைக் குறிக்கிறது. உடனடியாக ஆய்வு செய்ய பணியாளரை அனுப்பவும்."
    else:
        explanation_en = f"This alert indicates that the {zone_name} is losing roughly {deviation:.2f} liters of water beyond our baseline hydraulic model, pointing to an active leak or continuously running fixture. Please dispatch a technician immediately to inspect restrooms and mechanical rooms, and isolate zone shut-off valves if necessary to locate the source."
        explanation_ta = f"{zone_name} பகுதியில் சுமார் {deviation:.2f} லிட்டர் நீர் கசிவு ஏற்படுவதாக இந்த எச்சரிக்கை குறிக்கிறது. கசிவின் மூலத்தைக் கண்டறிய கழிப்பறைகள் மற்றும் இயந்திர அறைகளை ஆய்வு செய்ய பணியாளரை அனுப்பவும்."

    if not api_key or api_key == "your_key_here":
        return explanation_en, explanation_ta

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
    prompt = f"You are an expert facilities management assistant for a campus water system. An alert has been generated for the {zone_name}. Severity: {severity}. Deviation: {deviation:.2f} liters/level. Provide a short, human-readable explanation of what this means and suggest 1-2 immediate maintenance actions. Keep it under 3 sentences."
    
    try:
        response = model.generate_content(prompt)
        explanation_en = response.text
    except Exception as e:
        pass

    return explanation_en, explanation_ta
