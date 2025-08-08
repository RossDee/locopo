#!/usr/bin/env python3

print("🏪 Testing Willys eReklamblad...")

try:
    import requests
    
    url = "https://ereklamblad.se/Willys"
    print(f"📡 Loading: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    response = session.get(url, timeout=15)
    print(f"📊 Status: {response.status_code}")
    print(f"📄 Content Length: {len(response.text)} chars")
    
    if response.status_code == 200:
        print("✅ Successfully loaded Willys page")
        
        # Check for basic content
        content_lower = response.text.lower()
        
        if 'willys' in content_lower:
            print("✅ Contains 'willys' branding")
        
        if 'app-data' in content_lower:
            print("✅ Contains 'app-data' elements")
        
        if 'publication' in content_lower:
            print("✅ Contains 'publication' references")
            
        # Count occurrences of key terms
        pub_count = content_lower.count('publication')
        offer_count = content_lower.count('offer')
        id_count = content_lower.count('"id"')
        
        print(f"📊 Content analysis:")
        print(f"   'publication' appears {pub_count} times")
        print(f"   'offer' appears {offer_count} times")
        print(f"   '\"id\"' appears {id_count} times")
        
        # Show first 1000 characters
        print(f"\n📝 First 1000 characters:")
        print("-" * 50)
        print(response.text[:1000])
        print("-" * 50)
        
    else:
        print(f"❌ Failed to load page: {response.status_code}")
        
except Exception as e:
    print(f"💥 Error: {e}")
    import traceback
    traceback.print_exc()

print("🏁 Analysis complete!")
