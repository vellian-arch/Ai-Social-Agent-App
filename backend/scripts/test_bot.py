import os
from ai_engine import generate_ai_response
from database import init_db

def run_test():
    # 1. Ensure the database exists
    init_db()
    
    print("🧪 AI Social Agent - Simulation Tool")
    print("------------------------------------")
    
    # 2. Setup the test scenario
    biz_id = "1470862171282219"
    test_user = "TEST_USER_001"
    
    platforms = {
        "1": "WhatsApp",
        "2": "Facebook",
        "3": "Instagram",
        "4": "YouTube",
        "5": "TikTok"
    }
    
    print("Select a platform to simulate:")
    for key, name in platforms.items():
        print(f"{key}. {name}")
        
    choice = input("\nEnter number (1-5): ")
    platform_name = platforms.get(choice, "WhatsApp")
    
    user_msg = input(f"\nType a message to send to the {platform_name} AI: ")
    
    print(f"\n🤖 AI is thinking (simulating {platform_name} environment)...")
    
    # 3. Call the actual AI Engine
    reply = generate_ai_response(biz_id, test_user, user_msg, platform=platform_name)
    
    print(f"\n✨ AI Response: {reply}")
    print("\n✅ Check your Dashboard! The interaction should now be visible.")

if __name__ == "__main__":
    run_test()