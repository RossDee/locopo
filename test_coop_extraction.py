#!/usr/bin/env python3

import requests
import json
import re
from bs4 import BeautifulSoup

def analyze_coop_offers():
    """Analyze Coop offers and test extraction"""
    
    print("🛒 Coop eReklamblad Analysis")
    print("=" * 50)
    
    # Setup session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    # Coop details
    publication_id = "suVwNFKv"
    base_url = "https://ereklamblad.se"
    coop_url = f"{base_url}/Coop?publication={publication_id}"
    
    try:
        print(f"📡 Loading: {coop_url}")
        response = session.get(coop_url, timeout=15)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📄 Length: {len(response.text)} chars")
        print()
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract offer IDs from app-data
            print("🔍 Extracting offer IDs from app-data...")
            offer_ids = set()
            
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            for element in app_data_elements:
                try:
                    data_content = element.get_text().strip()
                    if data_content:
                        json_data = json.loads(data_content)
                        
                        # Recursively search for offer IDs
                        def extract_ids(obj):
                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    if key.lower() in ['id', 'offerid', 'offer_id'] and isinstance(value, str) and len(value) >= 10:
                                        offer_ids.add(value)
                                    else:
                                        extract_ids(value)
                            elif isinstance(obj, list):
                                for item in obj:
                                    extract_ids(item)
                        
                        extract_ids(json_data)
                        
                except json.JSONDecodeError:
                    # Fallback to regex
                    patterns = [
                        r'"id"\s*:\s*"([a-zA-Z0-9_-]{10,})"',
                        r'"offerId"\s*:\s*"([a-zA-Z0-9_-]{10,})"',
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, data_content)
                        offer_ids.update(matches)
                except Exception as e:
                    print(f"   ⚠️ Error processing app-data: {e}")
            
            print(f"✅ Found {len(offer_ids)} offer IDs")
            
            if offer_ids:
                print("\n📋 Sample offer IDs:")
                sample_ids = list(offer_ids)[:10]
                for i, offer_id in enumerate(sample_ids, 1):
                    print(f"   {i:2d}. {offer_id}")
                
                if len(offer_ids) > 10:
                    print(f"   ... and {len(offer_ids) - 10} more")
                
                # Test extracting data from a few offers
                print(f"\n🧪 Testing offer data extraction...")
                
                test_offers = list(offer_ids)[:3]  # Test first 3 offers
                successful_extractions = 0
                
                for i, offer_id in enumerate(test_offers, 1):
                    print(f"\n🔍 Testing offer {i}: {offer_id}")
                    
                    # Build offer URL
                    offer_url = f"{base_url}/Coop?publication={publication_id}&offer={offer_id}"
                    
                    try:
                        offer_response = session.get(offer_url, timeout=10)
                        print(f"   📡 Status: {offer_response.status_code}")
                        
                        if offer_response.status_code == 200:
                            offer_soup = BeautifulSoup(offer_response.text, 'html.parser')
                            
                            # Extract title
                            title_tag = offer_soup.find('title')
                            if title_tag:
                                title = title_tag.get_text().strip()
                                # Clean up title
                                title = re.sub(r'\s*från\s*Coop.*$', '', title)
                                title = re.sub(r'\s*-\s*Coop.*$', '', title)
                                title = re.sub(r'\s*\|\s*eReklamblad.*$', '', title)
                                print(f"   📦 Product: {title}")
                            
                            # Look for app-data in offer page
                            offer_app_data = offer_soup.find_all(id=lambda x: x and 'app-data' in x)
                            if offer_app_data:
                                for app_element in offer_app_data:
                                    try:
                                        app_content = app_element.get_text().strip()
                                        if app_content:
                                            app_json = json.loads(app_content)
                                            
                                            # Look for price and other data
                                            def find_offer_data(obj, target_id):
                                                if isinstance(obj, dict):
                                                    # Check if this object matches our offer
                                                    if 'id' in obj and obj['id'] == target_id:
                                                        price = None
                                                        for price_key in ['price', 'currentPrice', 'salePrice']:
                                                            if price_key in obj:
                                                                try:
                                                                    price = float(str(obj[price_key]).replace(',', '.'))
                                                                    break
                                                                except:
                                                                    pass
                                                        
                                                        if price:
                                                            print(f"   💰 Price: {price} SEK")
                                                        
                                                        # Look for description
                                                        for desc_key in ['description', 'productDescription']:
                                                            if desc_key in obj and obj[desc_key]:
                                                                desc = str(obj[desc_key])[:100]
                                                                if len(str(obj[desc_key])) > 100:
                                                                    desc += "..."
                                                                print(f"   📝 Description: {desc}")
                                                                break
                                                        
                                                        return True
                                                    
                                                    # Continue searching
                                                    for value in obj.values():
                                                        if find_offer_data(value, target_id):
                                                            return True
                                                elif isinstance(obj, list):
                                                    for item in obj:
                                                        if find_offer_data(item, target_id):
                                                            return True
                                                return False
                                            
                                            if find_offer_data(app_json, offer_id):
                                                successful_extractions += 1
                                                print(f"   ✅ Extraction successful!")
                                            
                                    except json.JSONDecodeError:
                                        continue
                                    except Exception as e:
                                        print(f"   ⚠️ Error parsing app-data: {e}")
                                        continue
                        else:
                            print(f"   ❌ Failed to load offer page")
                            
                    except Exception as e:
                        print(f"   💥 Error testing offer: {e}")
                
                print(f"\n📊 Results Summary:")
                print(f"   📋 Total offers found: {len(offer_ids)}")
                print(f"   ✅ Successful extractions: {successful_extractions}/{len(test_offers)}")
                print(f"   📈 Success rate: {(successful_extractions/len(test_offers))*100:.1f}%")
                
                # Return some sample offer IDs for further testing
                return list(offer_ids)
                
            else:
                print("❌ No offer IDs found")
                return []
        else:
            print(f"❌ Failed to load publication page: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    coop_offers = analyze_coop_offers()
    
    if coop_offers:
        print(f"\n🎯 Found {len(coop_offers)} Coop offers ready for integration!")
        print("✅ Coop eReklamblad scraping is feasible!")
    else:
        print("\n❌ No offers found - need further investigation")
