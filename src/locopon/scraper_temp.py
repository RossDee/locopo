#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
eReklamblad Complete Offer System
Based on discoveries: Individual offer pages contain complete data via app-data
Strategy: Build a complete system using known offer patterns and validate through testing
"""

import requests
from bs4 import BeautifulSoup
import json
import base64
import re
import time
import random
from datetime import datetime
from typing import List, Dict, Optional

class CompleteOfferSystem:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        }
        self.publication_id = "5X0fxUgs"
        self.base_url = f"https://ereklamblad.se/ICA-Maxi-Stormarknad?publication={self.publication_id}"
        
        # Known working offer IDs
        self.seed_offers = [
            "QKw9mX46Cnk4AU70rkjh3",
            "em9yvCtQ7djrVR83KsdMP", 
            "InFrprJEuqAJ3Jji23HdH",
            "Xehoqb8oZJH4Bf8_K416Q",
            "uEmpTS_uyXQ5tPdCuWNQv",
            "jHlSIkNLvbBAhvQYZCU8C",
            "lO8uQnRzNNjBWYDGzJzED", 
            "CQ8Lud1zrUa10bOa7xZs4",
            "eD8iZN3FEEHNxE3m8CQhC"
        ]
    
    def extract_offer_data_from_page(self, offer_id: str) -> Optional[Dict]:
        """Extract complete offer data from an offer page"""
        url = f"{self.base_url}&offer={offer_id}"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            app_data_elements = soup.find_all('app-data')
            
            # Look for the offer-specific data
            for elem in app_data_elements:
                if elem.text.strip():
                    try:
                        data = json.loads(elem.text)
                        
                        # Check if this contains our offer ID
                        data_str = json.dumps(data)
                        if offer_id in data_str:
                            # This is our offer data!
                            if isinstance(data, dict) and 'publicId' in data and data['publicId'] == offer_id:
                                return data
                                
                    except json.JSONDecodeError:
                        continue
            
            return None
            
        except Exception as e:
            print(f"❌ Error extracting offer {offer_id}: {e}")
            return None
    
    def test_offer_exists(self, offer_id: str) -> bool:
        """Test if an offer ID exists"""
        url = f"{self.base_url}&offer={offer_id}"
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def generate_potential_offer_ids(self, seed_offers: List[str], count: int = 100) -> List[str]:
        """Generate potential offer IDs based on known patterns"""
        print(f"🧬 Generating {count} potential offer IDs from {len(seed_offers)} seeds...")
        
        potential_ids = []
        
        # Analyze patterns from seed offers
        char_sets = {
            'letters_upper': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            'letters_lower': 'abcdefghijklmnopqrstuvwxyz', 
            'digits': '0123456789',
            'special': '_-'
        }
        
        for seed in seed_offers:
            # Generate variations by changing 1-2 characters
            for _ in range(count // len(seed_offers)):
                # Create variation
                seed_list = list(seed)
                
                # Change 1-2 positions randomly
                positions_to_change = random.sample(range(len(seed)), random.randint(1, 2))
                
                for pos in positions_to_change:
                    old_char = seed[pos]
                    
                    # Determine character type and pick from same type
                    if old_char.isupper():
                        new_char = random.choice(char_sets['letters_upper'])
                    elif old_char.islower():
                        new_char = random.choice(char_sets['letters_lower'])
                    elif old_char.isdigit():
                        new_char = random.choice(char_sets['digits'])
                    else:
                        new_char = random.choice(char_sets['special'])
                    
                    seed_list[pos] = new_char
                
                potential_id = ''.join(seed_list)
                if potential_id not in seed_offers:  # Don't include known ones
                    potential_ids.append(potential_id)
        
        # Remove duplicates
        unique_ids = list(set(potential_ids))
        print(f"Generated {len(unique_ids)} unique potential IDs")
        return unique_ids
    
    def discover_valid_offers(self, max_attempts: int = 200) -> List[str]:
        """Discover valid offers through systematic testing"""
        print(f"🔍 Discovering valid offers (max {max_attempts} attempts)...")
        
        # Start with known offers
        valid_offers = []
        
        # Test seed offers first
        print("Testing seed offers:")
        for offer in self.seed_offers:
            if self.test_offer_exists(offer):
                valid_offers.append(offer)
                print(f"  ✅ {offer}: Valid")
            else:
                print(f"  ❌ {offer}: Invalid")
        
        # Generate and test potential offers
        potential_offers = self.generate_potential_offer_ids(self.seed_offers, max_attempts)
        
        print(f"\nTesting {len(potential_offers)} generated offers (with rate limiting)...")
        tested = 0
        
        for i, offer_id in enumerate(potential_offers):
            if tested >= max_attempts:
                break
                
            if self.test_offer_exists(offer_id):
                valid_offers.append(offer_id)
                print(f"  ✅ {offer_id}: New valid offer found!")
            
            tested += 1
            
            # Progress indicator and rate limiting
            if tested % 10 == 0:
                print(f"  Progress: {tested}/{min(max_attempts, len(potential_offers))}")
            
            time.sleep(0.2)  # Rate limiting
        
        unique_valid = list(set(valid_offers))
        print(f"\n📊 Discovery complete: {len(unique_valid)} unique valid offers found")
        return unique_valid
    
    def extract_all_offer_data(self, offer_ids: List[str]) -> Dict[str, Dict]:
        """Extract complete data for all valid offers"""
        print(f"📦 Extracting complete data for {len(offer_ids)} offers...")
        
        offer_data = {}
        
        for i, offer_id in enumerate(offer_ids):
            print(f"  Extracting {i+1}/{len(offer_ids)}: {offer_id}")
            
            data = self.extract_offer_data_from_page(offer_id)
            if data:
                offer_data[offer_id] = data
                print(f"    ✅ Data extracted: {data.get('name', 'Unknown product')}")
            else:
                print(f"    ❌ Failed to extract data")
            
            time.sleep(1)  # Rate limiting
        
        return offer_data
    
    def save_results(self, offer_data: Dict[str, Dict]):
        """Save results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save complete offer data
        filename = f"complete_offers_data_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(offer_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Complete data saved to: {filename}")
        
        # Save summary
        summary = {
            'timestamp': timestamp,
            'publication_id': self.publication_id,
            'total_offers': len(offer_data),
            'offers': []
        }
        
        for offer_id, data in offer_data.items():
            summary['offers'].append({
                'id': offer_id,
                'name': data.get('name', 'Unknown'),
                'price': data.get('membershipPrice') or data.get('price'),
                'currency': data.get('currencyCode', 'SEK'),
                'valid_from': data.get('validFrom'),
                'valid_until': data.get('validUntil')
            })
        
        summary_filename = f"offers_summary_{timestamp}.json" 
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"📋 Summary saved to: {summary_filename}")
        
        return filename, summary_filename
    
    def run_complete_discovery(self, max_discovery_attempts: int = 50):
        """Run the complete offer discovery and extraction process"""
        print("🚀 eReklamblad Complete Offer Discovery System")
        print("="*80)
        print(f"Publication ID: {self.publication_id}")
        print(f"Max discovery attempts: {max_discovery_attempts}")
        print()
        
        # Step 1: Discover valid offers
        valid_offers = self.discover_valid_offers(max_discovery_attempts)
        
        if not valid_offers:
            print("❌ No valid offers discovered")
            return
        
        print(f"\n✅ Found {len(valid_offers)} valid offers")
        
        # Step 2: Extract complete data
        offer_data = self.extract_all_offer_data(valid_offers)
        
        if not offer_data:
            print("❌ No offer data extracted")
            return
        
        # Step 3: Save results
        data_file, summary_file = self.save_results(offer_data)
        
        # Step 4: Display summary
        print(f"\n📊 Final Results:")
        print(f"Valid offers discovered: {len(valid_offers)}")
        print(f"Offers with data extracted: {len(offer_data)}")
        print(f"Success rate: {len(offer_data)/len(valid_offers)*100:.1f}%")
        
        print(f"\nSample offers:")
        for i, (offer_id, data) in enumerate(list(offer_data.items())[:3]):
            name = data.get('name', 'Unknown')
            price = data.get('membershipPrice') or data.get('price', 'N/A')
            print(f"  {i+1}. {name} - {price} SEK (ID: {offer_id})")
        
        return offer_data

def main():
    """Main function"""
    system = CompleteOfferSystem()
    
    # Run with moderate discovery attempts to avoid overwhelming the server
    results = system.run_complete_discovery(max_discovery_attempts=30)
    
    if results:
        print(f"\n✅ System completed successfully!")
        print(f"Check the generated JSON files for complete results.")
    else:
        print(f"\n❌ System completed with no results")

if __name__ == "__main__":
    main()
