# Locopon 🇸🇪

Swedish retail coupon monitoring system for eReklamblad.se

## Features
- 🏙️ Multi-city retailer discovery (Stockholm, Sundsvall)
- 🛍️ Automated offer scraping from major Swedish retailers
- 📊 Data extraction and analysis

## Quick Start
```bash
pip install selenium beautifulsoup4 requests
python ereklamblad_discovery.py
```

## Supported Retailers
- ICA Maxi, Coop, Willys, Hemköp, Lidl
- JYSK, ÖoB, Hornbach, and 70+ others

## Results
- **Stockholm**: 76 retailers discovered
- **Sundsvall**: 73 retailers discovered
- **Success Rate**: 95%+ data extraction

## Files
- `ereklamblad_discovery.py` - Main discovery tool
- `compare_cities.py` - Multi-city analysis
- `stockholm_retailers.json` - Stockholm data
- `sundsvall_retailers.json` - Sundsvall data

## Documentation
📖 **[Complete Development Log & Technical Details](DEVELOPMENT_LOG.md)**

## License
MIT
