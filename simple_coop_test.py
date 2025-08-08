#!/usr/bin/env python3

print("🔍 Starting Coop analysis...")

try:
    import requests
    print("✅ Requests imported")
    
    url = "https://ereklamblad.se/Coop?publication=suVwNFKv"
    print(f"🌐 Testing URL: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    print("📡 Making request...")
    response = session.get(url, timeout=15)
    
    print(f"📊 Status Code: {response.status_code}")
    print(f"📄 Content Length: {len(response.text)} characters")
    
    if response.status_code == 200:
        print("✅ Request successful!")
        
        # Check for basic content
        content = response.text.lower()
        if 'coop' in content:
            print("✅ Contains 'coop'")
        if 'app-data' in content:
            print("✅ Contains 'app-data'")
        if 'publication' in content:
            print("✅ Contains 'publication'")
            
        # Show first 500 chars
        print("\n📝 First 500 characters:")
        print("-" * 50)
        print(response.text[:500])
        print("-" * 50)
    else:
        print(f"❌ Request failed with status {response.status_code}")
        
except Exception as e:
    print(f"💥 Error: {e}")
    import traceback
    traceback.print_exc()

print("🏁 Analysis complete!")
