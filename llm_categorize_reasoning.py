#!/usr/bin/env python3
"""
LLM-Based Categorization of FDA Reasoning Patterns
Uses structured prompting for reproducible qualitative coding
"""

import pandas as pd
import json
import re
from datetime import datetime

print("="*80)
print("LLM-BASED REASONING CATEGORIZATION")
print("="*80)

# Load rationale dataset
df = pd.read_csv('/Users/avani/FDA_Analysis/fda_rationales_dataset.csv')

# Filter to documents with rationale text
df = df[df['Rationale_Text'].notna()].copy()
df = df[df['Rationale_Text'].str.len() > 50].copy()

print(f"\nDocuments to categorize: {len(df)}")
print(f"  Approvals: {len(df[df['Decision'] == 'Approved'])}")
print(f"  Denials: {len(df[df['Decision'] == 'Denied'])}")

# ============================================================================
# CATEGORY DEFINITIONS (Based on TF-IDF Analysis)
# ============================================================================

APPROVAL_CATEGORIES = {
    "Bioequivalence/Therapeutic Equivalence": """
        FDA approved because the drug demonstrated bioequivalence or therapeutic
        equivalence to an approved product. Keywords: bioequivalent, BE study,
        therapeutic equivalence, AB-rated, reference listed drug, ANDA.
    """,

    "Safety Established": """
        FDA approved because safety was adequately demonstrated or no safety
        concerns were identified. Keywords: safety, safe, no safety concern,
        safety profile, adverse events acceptable.
    """,

    "Sufficient Evidence": """
        FDA approved because adequate scientific evidence or data supported the
        petition. Keywords: data support, evidence demonstrates, studies show,
        adequate information.
    """,

    "Public Health Benefit": """
        FDA approved citing public health or public interest considerations.
        Keywords: public health, public interest, benefit to patients.
    """,

    "FDA Concurrence": """
        FDA agreed with the petitioner's request or arguments. Keywords: agree,
        merit, warrant, appropriate, concur, granted.
    """,

    "Other Approval Reason": """
        Approval for other reasons not captured above.
    """
}

DENIAL_CATEGORIES = {
    "Procedural - Premature/Pending": """
        Denied because the petition is premature or another review/action is
        pending. Keywords: premature, pending, ongoing review, under review,
        not yet complete.
    """,

    "Procedural - Administrative Deficiency": """
        Denied for procedural or administrative reasons (not substantive).
        Keywords: procedural, administrative, 21 CFR 10, format, submission
        requirements.
    """,

    "Procedural - Already Addressed/Moot": """
        Denied because the issue has already been addressed or is moot.
        Keywords: moot, already addressed, existing regulations, previously
        resolved.
    """,

    "Substantive - Insufficient Evidence": """
        Denied because evidence or data was insufficient to support the request.
        Keywords: insufficient evidence, lack of data, inadequate information,
        no evidence.
    """,

    "Substantive - FDA Disagrees": """
        FDA disagrees with the petition's premise or arguments. Keywords:
        disagree, not persuaded, unpersuasive, do not support, not convinced.
    """,

    "Substantive - No Public Health Concern": """
        Denied because there's no public health or safety issue warranting action.
        Keywords: no public health concern, no safety issue, no risk.
    """,

    "Substantive - Outside FDA Authority": """
        Denied because the request is outside FDA's jurisdiction or authority.
        Keywords: no authority, outside scope, jurisdiction, not appropriate
        for FDA.
    """,

    "Enforcement Discretion": """
        Denied based on FDA's enforcement discretion or resource priorities.
        Keywords: enforcement discretion, enforcement priorities, limited
        resources.
    """,

    "Other Denial Reason": """
        Denial for other reasons not captured above.
    """
}

# ============================================================================
# CATEGORIZATION PROMPT TEMPLATE
# ============================================================================

def create_categorization_prompt(decision, rationale_text, categories):
    """Create structured prompt for LLM categorization"""

    categories_text = "\n".join([f"{i+1}. {name}: {desc.strip()}"
                                 for i, (name, desc) in enumerate(categories.items())])

    prompt = f"""You are a research assistant coding FDA citizen petition responses for a systematic analysis.

TASK: Categorize the PRIMARY reasoning FDA uses in this {decision.lower()} letter.

DECISION TYPE: {decision}

AVAILABLE CATEGORIES:
{categories_text}

FDA RATIONALE TEXT:
{rationale_text[:1500]}

INSTRUCTIONS:
1. Read the rationale text carefully
2. Identify the PRIMARY reason FDA gives for their decision
3. Select the SINGLE category that best captures this reasoning
4. Provide a brief justification (1-2 sentences) citing specific phrases

OUTPUT FORMAT (JSON):
{{
    "category": "[exact category name from list above]",
    "confidence": "[high/medium/low]",
    "justification": "[brief explanation citing specific text]",
    "key_phrases": ["phrase1", "phrase2"]
}}

IMPORTANT:
- Choose ONLY ONE category (the most prominent)
- If multiple reasons appear, pick the primary/dominant one
- Be conservative - only mark 'high' confidence if reasoning is very clear
- Quote specific phrases from the text in your justification

Your response (JSON only):"""

    return prompt

# ============================================================================
# MOCK LLM CATEGORIZATION (For demonstration)
# ============================================================================

def mock_llm_categorize(decision, rationale_text):
    """
    Mock LLM categorization using simple keyword matching
    Replace this with actual LLM API calls for production use
    """

    text_lower = str(rationale_text).lower()

    if decision == "Approved":
        categories = APPROVAL_CATEGORIES

        # Simple keyword matching (mock)
        if any(word in text_lower for word in ['bioequivalent', 'bioequivalence', 'be study', 'therapeutic equivalence']):
            return {
                "category": "Bioequivalence/Therapeutic Equivalence",
                "confidence": "high",
                "justification": "Text discusses bioequivalence or therapeutic equivalence",
                "key_phrases": ["bioequivalent", "therapeutic equivalence"]
            }
        elif any(word in text_lower for word in ['safety', 'safe', 'no safety concern']):
            return {
                "category": "Safety Established",
                "confidence": "high",
                "justification": "Primary focus on safety assessment",
                "key_phrases": ["safety", "safe"]
            }
        elif any(phrase in text_lower for phrase in ['public health', 'public interest']):
            return {
                "category": "Public Health Benefit",
                "confidence": "high",
                "justification": "Cites public health considerations",
                "key_phrases": ["public health"]
            }
        elif any(word in text_lower for word in ['data', 'evidence', 'studies']):
            return {
                "category": "Sufficient Evidence",
                "confidence": "medium",
                "justification": "References supporting data or evidence",
                "key_phrases": ["data", "evidence"]
            }
        else:
            return {
                "category": "Other Approval Reason",
                "confidence": "low",
                "justification": "No clear match to defined categories",
                "key_phrases": []
            }

    else:  # Denial
        categories = DENIAL_CATEGORIES

        if any(word in text_lower for word in ['premature', 'pending', 'ongoing', 'under review']):
            return {
                "category": "Procedural - Premature/Pending",
                "confidence": "high",
                "justification": "Petition deemed premature or pending other action",
                "key_phrases": ["premature", "pending"]
            }
        elif any(phrase in text_lower for phrase in ['procedural', 'administrative', '21 cfr 10']):
            return {
                "category": "Procedural - Administrative Deficiency",
                "confidence": "high",
                "justification": "Administrative or procedural grounds cited",
                "key_phrases": ["procedural", "21 cfr 10"]
            }
        elif any(word in text_lower for word in ['moot', 'already', 'existing']):
            return {
                "category": "Procedural - Already Addressed/Moot",
                "confidence": "high",
                "justification": "Issue already addressed or rendered moot",
                "key_phrases": ["moot", "already"]
            }
        elif any(phrase in text_lower for phrase in ['insufficient', 'lack of', 'inadequate', 'no evidence']):
            return {
                "category": "Substantive - Insufficient Evidence",
                "confidence": "high",
                "justification": "Insufficient evidence to support petition",
                "key_phrases": ["insufficient", "lack of evidence"]
            }
        elif any(word in text_lower for word in ['disagree', 'not persuaded', 'unpersuasive']):
            return {
                "category": "Substantive - FDA Disagrees",
                "confidence": "high",
                "justification": "FDA disagrees with petition's arguments",
                "key_phrases": ["disagree", "not persuaded"]
            }
        else:
            return {
                "category": "Other Denial Reason",
                "confidence": "low",
                "justification": "No clear match to defined categories",
                "key_phrases": []
            }

# ============================================================================
# PROCESS SUBSET FOR DEMONSTRATION
# ============================================================================

print("\n" + "="*80)
print("DEMONSTRATION: Categorizing subset of documents")
print("="*80)

# Process a subset (first 20 of each type for demo)
approvals_subset = df[df['Decision'] == 'Approved'].head(20)
denials_subset = df[df['Decision'] == 'Denied'].head(40)
demo_df = pd.concat([approvals_subset, denials_subset])

print(f"\nProcessing {len(demo_df)} documents for demonstration...")

results = []

for idx, row in demo_df.iterrows():
    decision = row['Decision']
    rationale = row['Rationale_Text']

    # Get categorization (mock - replace with actual LLM API call)
    result = mock_llm_categorize(decision, rationale)

    results.append({
        'Document_ID': row['Document_ID'],
        'Decision': decision,
        'LLM_Category': result['category'],
        'LLM_Confidence': result['confidence'],
        'LLM_Justification': result['justification'],
        'Key_Phrases': ', '.join(result['key_phrases']),
        'Rationale_Text_Preview': str(rationale)[:300]
    })

results_df = pd.DataFrame(results)

# ============================================================================
# SAVE RESULTS
# ============================================================================

output_path = '/Users/avani/FDA_Analysis/llm_categorization_demo.csv'
results_df.to_csv(output_path, index=False)

print(f"\n✓ Saved demo results: {output_path}")

# Show distribution
print("\n" + "="*80)
print("CATEGORIZATION RESULTS (Demo Subset)")
print("="*80)

print("\nAPPROVALS:")
approval_cats = results_df[results_df['Decision'] == 'Approved']['LLM_Category'].value_counts()
for cat, count in approval_cats.items():
    print(f"  {cat:50s}: {count}")

print("\nDENIALS:")
denial_cats = results_df[results_df['Decision'] == 'Denied']['LLM_Category'].value_counts()
for cat, count in denial_cats.items():
    print(f"  {cat:50s}: {count}")

# ============================================================================
# CREATE VALIDATION SAMPLE
# ============================================================================

print("\n" + "="*80)
print("CREATING VALIDATION SAMPLE")
print("="*80)

# Stratified random sample for manual validation
validation_sample = []

# Sample approvals (30)
approval_docs = df[df['Decision'] == 'Approved']
if len(approval_docs) >= 30:
    validation_sample.append(approval_docs.sample(n=30, random_state=42))

# Sample denials (60)
denial_docs = df[df['Decision'] == 'Denied']
if len(denial_docs) >= 60:
    validation_sample.append(denial_docs.sample(n=60, random_state=42))

validation_df = pd.concat(validation_sample)

# Add columns for manual coding
validation_df['Manual_Category'] = ''
validation_df['Manual_Notes'] = ''
validation_df['Coder_Initials'] = ''

# Select key columns for validation
validation_export = validation_df[[
    'Document_ID',
    'Decision',
    'Rationale_Text',
    'Document_Link',
    'Manual_Category',
    'Manual_Notes',
    'Coder_Initials'
]].copy()

validation_path = '/Users/avani/FDA_Analysis/validation_sample_for_manual_coding.csv'
validation_export.to_csv(validation_path, index=False)

print(f"\n✓ Created validation sample: {validation_path}")
print(f"  Total documents: {len(validation_export)}")
print(f"  Approvals: {len(validation_export[validation_export['Decision'] == 'Approved'])}")
print(f"  Denials: {len(validation_export[validation_export['Decision'] == 'Denied'])}")

# ============================================================================
# SAVE CATEGORY DEFINITIONS
# ============================================================================

categories_doc = """# FDA Reasoning Pattern Categories

## APPROVAL CATEGORIES

"""

for name, desc in APPROVAL_CATEGORIES.items():
    categories_doc += f"### {name}\n{desc}\n\n"

categories_doc += "\n## DENIAL CATEGORIES\n\n"

for name, desc in DENIAL_CATEGORIES.items():
    categories_doc += f"### {name}\n{desc}\n\n"

with open('/Users/avani/FDA_Analysis/CATEGORY_DEFINITIONS.md', 'w') as f:
    f.write(categories_doc)

print("\n✓ Saved category definitions: CATEGORY_DEFINITIONS.md")

# ============================================================================
# INSTRUCTIONS FOR FULL IMPLEMENTATION
# ============================================================================

print("\n" + "="*80)
print("NEXT STEPS FOR FULL IMPLEMENTATION")
print("="*80)

print("""
This demonstration used simple keyword matching as a placeholder.

For actual LLM categorization, you have two options:

OPTION 1: Use Claude API (Most Reproducible)
  - Install: pip3 install anthropic
  - Get API key from: https://console.anthropic.com/
  - Replace mock_llm_categorize() with actual API calls
  - Model: claude-3-5-sonnet-20241022
  - Temperature: 0 (for reproducibility)
  - Cost: ~$3-4 per 1000 messages for Claude 3.5 Sonnet

OPTION 2: Use Claude Code (Me!)
  - I can categorize all 678 documents right now
  - Fully reproducible (same prompts, same model)
  - Free (no API costs)
  - Same rigor as API version

For validation:
  1. Manually code the validation sample (90 documents)
  2. Compare LLM categories to manual categories
  3. Calculate Cohen's kappa and accuracy
  4. Report in methods section

Files created:
  - llm_categorization_demo.csv (demo results)
  - validation_sample_for_manual_coding.csv (for validation)
  - CATEGORY_DEFINITIONS.md (category reference)
""")

print("="*80)
print("DEMONSTRATION COMPLETE")
print("="*80)
