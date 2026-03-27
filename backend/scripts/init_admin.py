import sqlite3
import os
from dotenv import load_dotenv

DB_PATH = "ai_business_memory.db"

def setup_admin():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if admin already exists
    cursor.execute("SELECT email FROM users WHERE email = ?", ("admin@test.com",))
    if cursor.fetchone():
        print("ℹ️ Admin user already exists.")
    else:
        # Create admin user with plain password (to match frontend demo)
        # Tokens can be pulled from environment if needed
        whatsapp_token = os.getenv("WHATSAPP_TOKEN", "dummy_whatsapp_token")
        fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN", "dummy_fb_token")
        
        cursor.execute("""
            INSERT INTO users (
                email, password, subscription_status, 
                phone_id, fb_page_id, tiktok_open_id,
                whatsapp_token, fb_page_token
            ) VALUES (?, ?, 'active', ?, ?, ?, ?, ?)
        """, (
            "admin@test.com", 
            "password123",
            "admin_001",
            "fb_page_123",
            "tiktok_open_123",
            whatsapp_token,
            fb_token
        ))
        conn.commit()
        print("✅ Admin account created: admin@test.com")

    conn.close()

if __name__ == "__main__":
    load_dotenv()
    setup_admin()