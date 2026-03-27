import sqlite3
import os
from datetime import datetime

DB_PATH = "ai_business_memory.db"

def seed_products():
    """Insert sample products for the admin user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # First, get the admin user's email (assuming it exists)
    cursor.execute("SELECT email FROM users WHERE email = 'saintvellian@gmail.com'")
    admin = cursor.fetchone()
    if not admin:
        print("❌ Admin user not found. Run database.py first.")
        return

    admin_email = admin[0]

    # Clear existing products for this user (optional)
    cursor.execute("DELETE FROM products WHERE user_email = ?", (admin_email,))

    # Sample products
    sample_products = [
        ("Wireless Headphones", "99.99", "Premium noise-cancelling wireless headphones with 30-hour battery life.", "Electronics", "audio,wireless,premium", ""),
        ("Leather Jacket", "199.99", "Genuine leather jacket, available in black and brown.", "Fashion", "leather,men,women", ""),
        ("Smart Watch", "249.99", "Fitness tracker with heart rate monitor and GPS.", "Electronics", "fitness,wearable", ""),
        ("Yoga Mat", "29.99", "Eco-friendly non-slip yoga mat, 6mm thickness.", "Sports", "yoga,fitness", ""),
        ("Coffee Maker", "79.99", "12-cup programmable coffee maker with thermal carafe.", "Home", "kitchen,coffee", ""),
    ]

    for name, price, desc, cat, tags, media in sample_products:
        cursor.execute('''
            INSERT INTO products (user_email, name, price, description, category, tags, media_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (admin_email, name, price, desc, cat, tags, media, datetime.now().isoformat()))

    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(sample_products)} sample products for {admin_email}")

def seed_clients():
    """Insert sample onboarded clients for the admin user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users WHERE email = 'saintvellian@gmail.com'")
    admin = cursor.fetchone()
    if not admin:
        print("❌ Admin user not found.")
        return

    admin_email = admin[0]

    cursor.execute("DELETE FROM clients WHERE user_email = ?", (admin_email,))

    sample_clients = [
        ("Acme Corp", "contact@acme.com", "+1234567890", "Acme Corporation", "WhatsApp,Email", 92, "Interested in bulk electronics", datetime.now().isoformat()),
        ("TechStart", "info@techstart.io", "+1987654321", "TechStart Inc", "Instagram,Facebook", 78, "Looking for marketing automation", datetime.now().isoformat()),
        ("GreenLife", "hello@greenlife.com", "+1122334455", "GreenLife Org", "Telegram", 85, "Eco-friendly products inquiry", datetime.now().isoformat()),
    ]

    for name, email, phone, company, platforms, score, notes, date in sample_clients:
        cursor.execute('''
            INSERT INTO clients (user_email, name, email, phone, company, platforms, score, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (admin_email, name, email, phone, company, platforms, score, notes, date))

    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(sample_clients)} sample clients for {admin_email}")

if __name__ == "__main__":
    seed_products()
    seed_clients()