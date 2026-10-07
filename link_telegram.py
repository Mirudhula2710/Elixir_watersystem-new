import sqlite3
import sys

def update_worker_chat_id(chat_id):
    conn = sqlite3.connect("instance/users.db")
    c = conn.cursor()
    c.execute("UPDATE user SET telegram_chat_id = ? WHERE username = 'worker1'", (str(chat_id),))
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Successfully linked Telegram Chat ID '{chat_id}' to Worker 1 (+91 8122102645)!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        update_worker_chat_id(sys.argv[1])
    else:
        print("Usage: python link_telegram.py <CHAT_ID>")
