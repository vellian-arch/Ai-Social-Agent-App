import sqlite3
import hashlib
from database import DB_PATH  # reuse the same path

def hash_password(password):
    """Simple SHA-256 hashing for basic security."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_business(email, password, phone_id=None, fb_page_id=None, tiktok_open_id=None, message_limit=1000):
    """
    Register a new business user. Only email and password are required.
    Platform IDs are optional and can be added later via connection flows.
    """
    hashed_pw = hash_password(password)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insert only the fields we have; others will use defaults or NULL
        query = """
            INSERT INTO users (
                email, password, phone_id, fb_page_id, tiktok_open_id,
                message_limit, subscription_status
            ) VALUES (?, ?, ?, ?, ?, ?, 'active')
        """
        cursor.execute(query, (email, hashed_pw, phone_id, fb_page_id, tiktok_open_id, message_limit))
        conn.commit()
        print(f"✅ Success: {email} is now registered!")
        if phone_id:
            print(f"📞 WhatsApp Phone ID: {phone_id}")
        if fb_page_id:
            print(f"📘 Facebook Page ID: {fb_page_id}")
        if tiktok_open_id:
            print(f"🎵 TikTok Open ID: {tiktok_open_id}")
        
    except sqlite3.IntegrityError:
        print(f"❌ Error: The email '{email}' is already registered.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("--- Saintvellian AI User Registration ---")
    user_email = input("Enter Business Email: ")
    user_pass = input("Enter Password: ")
    phone_id = input("Enter Meta/WhatsApp Phone ID (optional, press Enter to skip): ").strip() or None
    fb_page_id = input("Enter Facebook Page ID (optional): ").strip() or None
    tiktok_open_id = input("Enter TikTok Open ID (optional): ").strip() or None
    
    register_business(user_email, user_pass, phone_id, fb_page_id, tiktok_open_id)