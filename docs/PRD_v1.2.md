# Product Requirements Document (PRD)
**Project:** JD-Fit Evaluator  
**Owner:** FoundryHR / Internal HR AI Tooling  
**Status:** Draft v1.2 (Living Document)  
**Last Updated:** 2025-09-30  

---

## 1. Vision & Goals
Recruiters and HR teams waste time manually reviewing resumes. We want an AI-assisted system that:  
- Pulls candidates from **Greenhouse** (and later, other ATS sources).  
- Compares each applicant **against the job description (JD)**, not against each other.  
- Produces a **Fit Score (0–100)** plus a **rationale (“why”)**.  
- Uses **multi-signal evaluation** (titles, industries, tenure, skills, context).  
- Learns over time from historical **hire vs. reject** decisions.  

**Goal:** Handle **hundreds of applicants per role** with scalable evaluation.  
**MVP Target:** Run ~200 candidates for the **Agoric Senior Product Designer (Web3/DeFi)** role.  

---

## 2. Company Context (Agoric)
- **Industry:** Web3, DeFi, Blockchain, Orchestration.  
- **Product:** Ymax — intelligent DeFi command center (multi-protocol orchestration).  
- **Technology themes:** crypto wallets, smart contracts, decentralized protocols, AI/LLM-driven optimization.  
- **Culture:** remote-first, collaboration across product, engineering, marketing.  

These signals must be **baked into the taxonomy and JD profile extraction** for MVP.  

---

## 3. Job Description (Target Role)
**Title:** Senior Product Designer (Web3/DeFi)  
**Key Responsibilities:**  
- Design end-to-end flows for DeFi orchestration.  
- Lead usability testing and synthesize findings.  
- Translate DeFi complexity into clear interactions.  
- Enable workflows for multi-protocol strategies via single signature.  
- Partner on AI-driven design enhancements.  

**Requirements:**  
- 5+ years UX design; 2+ in Web3 (DeFi strongly preferred).  
- Strong knowledge of wallets, smart contracts, protocols.  
- Hands-on usability testing.  
- Collaboration across product/engineering/marketing.  
- US hours (remote-first).  

---

## 4. MVP Fit Signals
**Title/Role:** Product Designer, UX Designer, Senior Designer, Senior Product Designer.  
**Industry:** Web3, DeFi, Crypto, Fintech, SaaS.  
**Skills/Experience:**  
- Wallet flows, smart contracts, decentralized protocols.  
- Usability testing, end-to-end UX flows, DeFi strategy design.  
- Independent design ownership, cross-functional collaboration.  
- AI/LLM product experience = bonus.  
**Tenure:** 5+ years UX, 2+ years Web3/crypto.  
**Recency:** Relevant Web3/DeFi design within last 3 years.  

---

## 5. Key Features (MVP Scope)
- **Ingestion:** Greenhouse API → parse ~200 resumes for this JD.  
- **Stint Extraction:** Normalize roles, companies, industries.  
- **Taxonomy Enrichment:** Add **Agoric**, **Ymax**, **Web3**, **DeFi**, **crypto wallets**, **smart contracts**.  
- **Scoring Engine:** Multi-signal weighted Fit Score (0–100).  
- **UI/UX:** Streamlit sliders + JD profile preloaded with this role.  
- **Training:** Allow labeling for eventual calibration (not required for MVP).  

---

## 6. Compliance & Ethics
- Keep resumes local (no external API).  
- Provide rationale for transparency.  
- Bias mitigation out of scope for MVP.  
- Version weights & checkpoints for reproducibility.  

---

## 7. Milestones
**MVP (Agoric Senior Product Designer role):**  
- Parse 200 candidates via Greenhouse.  
- Apply JD-aware scoring with DeFi/Web3 signals.  
- Output CSV/JSON with Fit Scores + rationale.  
- Deliver UI with JD preloaded.  

**Next:**  
- Expand taxonomy (wallet providers, protocol ecosystems).  
- Improve stint parsing accuracy.  
- Begin training with labels.  

**Future:**  
- Candidate_id-based training.  
- ATS note exports.  
- Bias mitigation.  
- Multi-JD and enterprise scaling.  

---

## 8. Open Questions
- How much to pre-train taxonomy with specific protocols (Uniswap, Aave, etc.) vs. general Web3 terms?  
- How to weight AI/LLM product design experience vs. DeFi design?  
- Should collaboration evidence (cross-functional teams) be modeled explicitly?  

---

## 9. Ownership
- **Owner:** FoundryHR product team.  
- **Partner:** Agoric (test case, Senior Product Designer role).  
- **Workflow:** PRD v1.2 in `/docs/` → updated with each sprint.  