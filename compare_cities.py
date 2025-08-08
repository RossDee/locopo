#!/usr/bin/env python3
"""
Sundsvall vs Stockholm Retailer Comparison Analysis
"""

import json

def load_retailers(filename):
    """Load retailers from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return []

def analyze_retailers(retailers, city_name):
    """Analyze retailer distribution"""
    print(f"\n🏪 {city_name} Retailer Analysis")
    print("=" * 50)
    
    print(f"📊 Total Retailers: {len(retailers)}")
    
    # Major food retailers
    food_chains = [
        'ICA Maxi', 'ICA Kvantum', 'ICA Supermarket', 'ICA Nära',
        'Coop', 'Stora Coop', 'Coop X:-TRA',
        'Willys', 'Willys Hemma',
        'Hemköp', 'City Gross', 'Lidl', 'Tempo', 'Matöppet'
    ]
    
    found_food_retailers = []
    for retailer in retailers:
        name = retailer.get('name', '')
        if any(chain in name for chain in food_chains):
            found_food_retailers.append(name)
    
    print(f"🛒 Major Food Retailers ({len(found_food_retailers)}):")
    for retailer in sorted(found_food_retailers):
        print(f"  • {retailer}")
    
    # Specialty retailers
    specialty_chains = [
        'JYSK', 'ILVA', 'Jula', 'jem & fix', 'Hornbach',
        'Lekia', 'ÖoB', 'thansen', 'Electrolux', 'Mio'
    ]
    
    found_specialty = []
    for retailer in retailers:
        name = retailer.get('name', '')
        if any(chain in name for chain in specialty_chains):
            found_specialty.append(name)
    
    print(f"🏬 Specialty Retailers ({len(found_specialty)}):")
    for retailer in sorted(found_specialty):
        print(f"  • {retailer}")
    
    return {
        'total': len(retailers),
        'food_retailers': found_food_retailers,
        'specialty_retailers': found_specialty
    }

def compare_cities():
    """Compare Stockholm and Sundsvall retailers"""
    print("🇸🇪 Swedish Cities Retailer Comparison")
    print("=" * 60)
    
    # Load data
    stockholm_retailers = load_retailers('stockholm_retailers.json')
    sundsvall_retailers = load_retailers('sundsvall_retailers.json')
    
    if not stockholm_retailers:
        print("❌ Stockholm data not found")
        return
    
    if not sundsvall_retailers:
        print("❌ Sundsvall data not found") 
        return
    
    # Analyze each city
    stockholm_analysis = analyze_retailers(stockholm_retailers, "Stockholm")
    sundsvall_analysis = analyze_retailers(sundsvall_retailers, "Sundsvall")
    
    # Comparison
    print(f"\n📊 City Comparison")
    print("=" * 50)
    print(f"Stockholm: {stockholm_analysis['total']} total retailers")
    print(f"Sundsvall:  {sundsvall_analysis['total']} total retailers")
    print(f"Difference: {stockholm_analysis['total'] - sundsvall_analysis['total']} more in Stockholm")
    
    # Common retailers
    stockholm_names = set(r.get('name', '') for r in stockholm_retailers)
    sundsvall_names = set(r.get('name', '') for r in sundsvall_retailers)
    
    common_retailers = stockholm_names.intersection(sundsvall_names)
    stockholm_only = stockholm_names - sundsvall_names
    sundsvall_only = sundsvall_names - stockholm_names
    
    print(f"\n🤝 Common Retailers ({len(common_retailers)}):")
    for retailer in sorted(common_retailers):
        if len(retailer) > 2:  # Filter out short/empty names
            print(f"  • {retailer}")
    
    print(f"\n🏢 Stockholm Only ({len(stockholm_only)}):")
    for retailer in sorted(list(stockholm_only)[:10]):  # Show first 10
        if len(retailer) > 2:
            print(f"  • {retailer}")
    
    print(f"\n🏔️ Sundsvall Only ({len(sundsvall_only)}):")
    for retailer in sorted(list(sundsvall_only)[:10]):  # Show first 10
        if len(retailer) > 2:
            print(f"  • {retailer}")

if __name__ == "__main__":
    compare_cities()
