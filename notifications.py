import os
import requests
import logging

logger = logging.getLogger(__name__)

MESSAGES = {
    'ta': {
        'title': 'புதிய பணி ஒதுக்கப்பட்டுள்ளது', # New Work Assigned
        'ticket_id': 'டிக்கெட் எண்', # Ticket ID
        'location': 'இடம் / மண்டலம்', # Location / Zone
        'severity': 'தீவிரம்', # Severity
        'deviation': 'வேறுபாடு', # Deviation
        'complaint': 'மாணவர் புகார்', # Student Complaint
        'routine': 'வழக்கமான பராமரிப்பு பணி', # Routine Maintenance
        'footer': 'பணியை தொடங்க அல்லது முடிக்க உங்கள் டேஷ்போர்டில் உள்நுழையவும்.' # Please log in to dashboard
    },
    'hi': {
        'title': 'नया कार्य सौंपा गया है',
        'ticket_id': 'टिकट आईडी',
        'location': 'स्थान / क्षेत्र',
        'severity': 'गंभीरता',
        'deviation': 'विचलन',
        'complaint': 'छात्र शिकायत',
        'routine': 'नियमित रखरखाव कार्य',
        'footer': 'स्थिति अपडेट करने के लिए कृपया अपने डैशबोर्ड में लॉगिन करें।'
    },
    'en': {
        'title': 'NEW TICKET ASSIGNED',
        'ticket_id': 'Ticket ID',
        'location': 'Location / Zone',
        'severity': 'Severity',
        'deviation': 'Deviation',
        'complaint': 'Student Complaint',
        'routine': 'Routine Maintenance / System Inspection',
        'footer': 'Please log in to your Worker Dashboard to update status.'
    }
}

def notify_worker_via_telegram(worker, ticket, title=None):
    """
    Sends a local push notification to a worker's phone via Telegram Bot API with regional language support.
    """
    if not worker or not getattr(worker, 'telegram_chat_id', None):
        logger.info(f"[TELEGRAM NOTIFICATION SKIPPED] Worker {getattr(worker, 'name', 'Unknown')} has no telegram_chat_id configured.")
        print(f"[LOCAL SIMULATED NOTIFICATION] Worker '{getattr(worker, 'name', 'Worker')}' assigned to Ticket #{ticket.id if ticket else 'N/A'}.")
        return False

    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.warning("[TELEGRAM NOTIFICATION SKIPPED] TELEGRAM_BOT_TOKEN environment variable is not set.")
        print(f"[LOCAL NOTIFICATION TRIGGERED] (Set TELEGRAM_BOT_TOKEN to send real phone notification to Chat ID: {worker.telegram_chat_id})")
        return False

    # Get language preferences (default to Tamil 'ta' if not set)
    lang = getattr(worker, 'preferred_language', 'ta') or 'ta'
    if lang not in MESSAGES:
        lang = 'ta'
    
    t = MESSAGES[lang]
    header = title if title else t['title']
    zone_name = ticket.zone.name if ticket.zone else "Unknown Zone"
    
    # Format details based on ticket type
    details = ""
    if ticket.alert:
        details = f"<b>{t['severity']}:</b> {ticket.alert.severity}\n<b>{t['deviation']}:</b> {ticket.alert.deviation} L"
    elif ticket.complaint:
        details = f"<b>{t['complaint']}:</b> {ticket.complaint.description}"
    else:
        details = t['routine']

    message = (
        f"🚨 <b>{header}</b> 🚨\n\n"
        f"<b>{t['ticket_id']}:</b> #{ticket.id}\n"
        f"<b>{t['location']}:</b> {zone_name}\n"
        f"{details}\n\n"
        f"<i>{t['footer']}</i>"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": worker.telegram_chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            logger.info(f"Successfully sent Telegram notification to worker {worker.name} ({lang})")
            return True
        else:
            logger.error(f"Failed to send Telegram message: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {e}")
        return False
