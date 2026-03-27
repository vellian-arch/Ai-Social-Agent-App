import multiprocessing
import time
from flask import Flask, request, jsonify
from youtube_bot import run_bot as start_youtube_engine
from database import save_lead_interaction, increment_usage, check_usage_limit
# Import your specific platform handlers here
# from tiktok_handler import handle_tiktok_event
# from meta_handler import handle_meta_event

app = Flask(__name__)

# --- 1. THE WEBHOOK RECEIVER (Real-time: WA, FB, IG, TikTok) ---
@app.route('/webhooks/all', methods=['POST'])
def universal_webhook():
    data = request.json
    platform = "Unknown"
    
    # Simple logic to detect source (Expand this as you add platforms)
    if 'object' in data and data['object'] == 'whatsapp_business_account':
        platform = "WhatsApp"
    elif 'tiktok_openid' in data or 'challenge' in data:
        platform = "TikTok"
    
    # SaaS Guard: Check usage before processing
    # (In a real app, you'd extract the user's email from the incoming ID)
    user_email = "admin@test.com" 
    
    if not check_usage_limit(user_email):
        return jsonify({"status": "limit_reached"}), 403

    print(f"📥 Incoming message on {platform}...")
    
    # Trigger AI logic and increment usage
    # process_ai_reply(data, platform)
    increment_usage(user_email)
    
    return jsonify({"status": "success"}), 200

def run_webhook_server():
    print("🌐 Webhook Server listening on port 5000...")
    app.run(port=5000, debug=False, use_reloader=False)

# --- 2. THE MASTER ORCHESTRATOR ---
if __name__ == "__main__":
    print("""
    =========================================
    🚀 Social Ai Agent - MASTER ENGINE
    =========================================
    """)

    # Create processes
    # Process A: The YouTube Loop (Runs every 5 mins)
    youtube_process = multiprocessing.Process(target=start_youtube_engine)
    
    # Process B: The Webhook Server (Stays open for WA/TikTok)
    webhook_process = multiprocessing.Process(target=run_webhook_server)

    # Start everything
    youtube_process.start()
    webhook_process.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down AI Engine...")
        youtube_process.terminate()
        webhook_process.terminate()
