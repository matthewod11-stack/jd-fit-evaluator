#!/usr/bin/env python3
"""
Test script to verify taxonomy changes for product designer and web3 signals
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_title_hints():
    """Test the updated TITLE_HINTS dictionary"""
    from etl.greenhouse import TITLE_HINTS, guess_titles_norm
    
    print("=== Testing TITLE_HINTS Structure ===")
    print("Available categories:", list(TITLE_HINTS.keys()))
    
    # Test product designer hints
    if "product_designer" in TITLE_HINTS:
        print(f"Product Designer keywords: {TITLE_HINTS['product_designer']}")
    
    # Test web3 signals
    if "web3_design_signals" in TITLE_HINTS:
        print(f"Web3 Design signals: {TITLE_HINTS['web3_design_signals']}")
    
    print("\n=== Testing guess_titles_norm Function ===")
    
    # Test product designer detection
    test_cases = [
        "Senior Product Designer at Apple",
        "UX Designer with 5 years experience", 
        "UI/UX Designer focused on mobile apps",
        "Interaction Designer at Google",
        "Design Lead for consumer products",
        "Product Designer working on DeFi protocols",
        "Senior UX Designer at Uniswap building wallet interfaces",
        "Designer with Web3 and blockchain experience",
        "Software Engineer", # Should not match
    ]
    
    for case in test_cases:
        result = guess_titles_norm(case)
        print(f"Text: '{case}'")
        print(f"  → Result: {result}")

def test_normalize_title():
    """Test the normalize_title function"""
    from parsing.stints import normalize_title
    
    print("\n=== Testing normalize_title Function ===")
    
    test_titles = [
        "Senior Product Designer",
        "UX Designer",
        "UI/UX Designer", 
        "Interaction Designer",
        "Experience Designer",
        "Design Lead",
        "Software Engineer",  # Should not be normalized
        "Product Manager",    # Should not be normalized
        None,                # Edge case
        "",                  # Edge case
    ]
    
    for title in test_titles:
        normalized = normalize_title(title)
        print(f"'{title}' → '{normalized}'")

def main():
    print("Testing taxonomy changes for product designer and web3 signals...\n")
    
    try:
        test_title_hints()
        test_normalize_title()
        print("\n🎉 All taxonomy tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)