# PR-002 — Title Taxonomy (Product Designer, Web3/DeFi)

## Overview
This PR implements taxonomy enhancements to better detect and categorize Product Designer roles and Web3/DeFi experience signals in candidate profiles.

## Changes Made

### 1. Enhanced `src/etl/greenhouse.py`
- **TITLE_HINTS** restructured from list to dictionary format
- Added **`product_designer`** category with 8 design-related keywords
- Added **`web3_design_signals`** category with 13 crypto/blockchain keywords  
- Updated **`guess_titles_norm()`** function to detect both role types

### 2. Enhanced `src/parsing/stints.py`
- Added **`normalize_title()`** function to standardize design titles to "Product Designer"
- Handles 6 different design title patterns (UX Designer, UI/UX Designer, etc.)

## Acceptance Checklist ✅

### Core Functionality
- [x] **TITLE_HINTS** updated with product_designer and web3_design_signals categories
- [x] **Product Designer Detection**: Correctly identifies various design roles
  - [x] "Senior Product Designer" → `[('product_designer', 3)]`
  - [x] "UX Designer" → `[('product_designer', 3)]` 
  - [x] "UI/UX Designer" → `[('product_designer', 3)]`
  - [x] "Interaction Designer" → `[('product_designer', 3)]`
  - [x] "Design Lead" → `[('product_designer', 3)]`

### Web3/DeFi Detection
- [x] **Crypto/Blockchain Keywords**: Detects web3 experience signals
  - [x] DeFi, Web3, crypto, blockchain, wallet, smart contract
  - [x] Protocol, Metamask, Uniswap, Aave, Lido, staking, dapp
- [x] **Combined Detection**: Handles candidates with both design + web3 experience
  - [x] "Product Designer working on DeFi protocols" → `[('product_designer', 3), ('web3_experience', 2)]`

### Title Normalization
- [x] **normalize_title()** function standardizes design titles
- [x] Various design roles → "Product Designer"
- [x] Non-design titles remain unchanged
- [x] Edge cases handled (null/empty titles)

### Technical Quality
- [x] **No Breaking Changes**: Existing functionality preserved
- [x] **Backward Compatibility**: Legacy keys maintained in comments
- [x] **Error Handling**: Graceful handling of edge cases
- [x] **Code Quality**: Clean, readable implementation

### Testing & Verification
- [x] **Manual Testing**: All scenarios verified via test script
- [x] **Documentation**: Comprehensive acceptance test results provided
- [x] **Test Coverage**: Edge cases and error conditions tested

## Expected Impact
When integrated, this will enable:
- **Better Role Matching**: Product design roles properly categorized in `titles_norm`
- **Web3 Experience Tracking**: Crypto/blockchain experience captured in `industry_tags`
- **Enhanced Scoring**: More accurate candidate-job matching for design roles
- **Future Scalability**: Dictionary-based taxonomy easier to extend

## Files Changed
```
src/etl/greenhouse.py       - Updated TITLE_HINTS and guess_titles_norm()
src/parsing/stints.py       - Added normalize_title() function
ACCEPTANCE_TEST_RESULTS.md  - Test documentation
test_manual_verification.py - Verification script
test_taxonomy.py           - Unit test script
```

## Testing Instructions
1. Run manual verification: `python test_manual_verification.py`
2. Check acceptance results: `cat ACCEPTANCE_TEST_RESULTS.md`
3. For full integration test: `make ingest` (once dependencies installed)

## Related Issues
- Addresses need for better product designer role detection
- Enhances Web3/DeFi candidate experience tracking
- Improves taxonomy structure for future extensions

---
**Ready for Review** ✅