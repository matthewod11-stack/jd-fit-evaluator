# Acceptance Test Results: feat/taxonomy-designer-web3

## Summary
Successfully implemented and verified taxonomy changes for product designer roles and web3/crypto experience detection.

## Changes Applied ✅

### 1. Updated `src/etl/greenhouse.py`
- **TITLE_HINTS** converted from list to dictionary format
- Added **product_designer** category with 8 design-related keywords:
  - "product designer", "senior product designer", "ux designer"
  - "senior ux designer", "ui/ux designer", "interaction designer"
  - "design lead", "experience designer"
- Added **web3_design_signals** category with 13 crypto/blockchain keywords:
  - "defi", "web3", "crypto", "blockchain", "wallet", "smart contract"
  - "protocol", "metamask", "uniswap", "aave", "lido", "staking", "dapp"
- **guess_titles_norm()** function updated to:
  - Detect product designer roles → returns `("product_designer", 3)`
  - Count web3 signals → returns `("web3_experience", count)` (max 3)

### 2. Updated `src/parsing/stints.py`
- Added **normalize_title()** function that:
  - Standardizes various design titles to "Product Designer"
  - Handles 6 different design title patterns
  - Returns original title if no match found

## Verification Results ✅

### Product Designer Detection
- ✅ "Senior Product Designer at Apple" → `[('product_designer', 3)]`
- ✅ "UX Designer with 5 years experience" → `[('product_designer', 3)]`
- ✅ "UI/UX Designer focused on mobile apps" → `[('product_designer', 3)]`
- ✅ "Interaction Designer at Google" → `[('product_designer', 3)]`
- ✅ "Design Lead for consumer products" → `[('product_designer', 3)]`

### Web3/Crypto Experience Detection
- ✅ "Product Designer working on DeFi protocols" → `[('product_designer', 3), ('web3_experience', 2)]`
- ✅ "Senior UX Designer at Uniswap building wallet interfaces" → `[('product_designer', 3), ('web3_experience', 2)]`
- ✅ "Designer with Web3 and blockchain experience at Metamask" → `[('web3_experience', 3)]`

### Title Normalization
- ✅ "Senior Product Designer" → "Product Designer"
- ✅ "UX Designer" → "Product Designer"
- ✅ "UI/UX Designer" → "Product Designer"
- ✅ "Interaction Designer" → "Product Designer"
- ✅ "Experience Designer" → "Product Designer"
- ✅ "Design Lead" → "Product Designer"
- ✅ Non-design titles remain unchanged

### Edge Cases
- ✅ "Software Engineer" → `[]` (no matches, as expected)
- ✅ Empty/null titles handled gracefully

## Expected Impact
When the full system runs (`make ingest`), candidates will now have:
- **titles_norm** including "Product Designer" entries for design roles
- **industry_tags** including "Web3/DeFi" signals for crypto experience
- Better matching for design roles against product design job descriptions
- Enhanced scoring for candidates with web3/blockchain experience

## Branch Status
- ✅ Branch created: `feat/taxonomy-designer-web3`
- ✅ Patches applied successfully
- ✅ Functionality verified through manual testing
- ✅ Ready for integration testing once dependencies are fully installed