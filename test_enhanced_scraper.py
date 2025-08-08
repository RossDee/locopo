#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_enhanced_scraper():
    """Test the enhanced scraper with known offer IDs"""
    try:
        from locopon.scraper import EreklamkladScraper
        
        print("🕷️ Testing Enhanced eReklamblad Scraper")
        print("=" * 50)
        
        scraper = EreklamkladScraper()
        
        # Test with known offer IDs from your analysis
        test_offers = [
            "em9yvCtQ7djrVR83KsdMP",  # Köksredskap
            "QKw9mX46Cnk4AU70rkjh3",  # Brie-, getost
            "InFrprJEuqAJ3Jji23HdH",  # Chokladkaka
            "uEmpTS_uyXQ5tPdCuWNQv",  # Vika Knäckebröd
            "Xehoqb8oZJH4Bf8_K416Q"   # Schampo, balsam, duschcreme
        ]
        
        print(f"📋 Testing {len(test_offers)} known offers...")
        print()
        
        successful_extractions = 0
        
        for i, offer_id in enumerate(test_offers, 1):
            print(f"🔍 Testing offer {i}/{len(test_offers)}: {offer_id}")
            
            try:
                # Test URL accessibility
                url = f"https://ereklamblad.se/ICA-Maxi-Stormarknad?publication=5X0fxUgs&offer={offer_id}"
                response = scraper.session.get(url, timeout=10)
                
                print(f"   📡 URL Status: {response.status_code}")
                print(f"   📄 Content Length: {len(response.text)} chars")
                
                if response.status_code == 200:
                    # Extract offer data
                    offer_data = scraper.extract_offer_data(offer_id)
                    
                    if offer_data:
                        successful_extractions += 1
                        print(f"   ✅ Extraction successful!")
                        print(f"   📦 Product: {offer_data.name}")
                        print(f"   💰 Price: {offer_data.price} {offer_data.currency}")
                        if offer_data.description:
                            desc = offer_data.description[:100] + "..." if len(offer_data.description) > 100 else offer_data.description
                            print(f"   📝 Description: {desc}")
                        if offer_data.image_url:
                            print(f"   🖼️ Image: {offer_data.image_url}")
                        print(f"   🏪 Store: {offer_data.business_name}")
                    else:
                        print(f"   ❌ Failed to extract offer data")
                else:
                    print(f"   ❌ Failed to access URL")
                    
            except Exception as e:
                print(f"   💥 Error testing {offer_id}: {e}")
            
            print()
        
        print("=" * 50)
        print(f"📊 Results Summary:")
        print(f"   ✅ Successful extractions: {successful_extractions}/{len(test_offers)}")
        print(f"   📈 Success rate: {(successful_extractions/len(test_offers))*100:.1f}%")
        
        if successful_extractions > 0:
            print("\n🎉 Enhanced scraper is working! Testing offer discovery...")
            
            # Test offer discovery
            discovered_offers = scraper.discover_offers(force_refresh=True)
            print(f"🔎 Discovered {len(discovered_offers)} total offers")
            
            # Show some discovered offers
            if discovered_offers:
                print(f"📋 Sample discovered offers:")
                for offer_id in discovered_offers[:10]:  # Show first 10
                    print(f"   - {offer_id}")
                    
                if len(discovered_offers) > 10:
                    print(f"   ... and {len(discovered_offers) - 10} more")
        else:
            print("\n❌ No successful extractions. Need to investigate further.")
        
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_scraper()
