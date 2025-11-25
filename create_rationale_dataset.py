#!/usr/bin/env python3
"""
Create Focused Rationale Dataset
Extract FDA's reasoning for each final response decision
"""

import pandas as pd
import re
import numpy as np

print("="*80)
print("CREATING FDA RATIONALE DATASET")
print("="*80)

# Load enhanced data
df = pd.read_csv('/Users/avani/FDA_Analysis/enhanced_fda_petitions.csv')

# Filter to final responses with decisions
final_responses = df[
    (df['Type of Document (Petition, Interim Response, Final Response)'] == 'Final Response') &
    (df['Mined_Response_Type'].notna()) &
    (df['text'].notna())
].copy()

print(f"\nProcessing {len(final_responses):,} final response documents")

# ============================================================================
# EXTRACT RATIONALE TEXT
# ============================================================================

def extract_rationale_text(text, decision_type):
    """
    Extract the specific section where FDA explains their decision.
    Returns up to 1000 characters of the key rationale section.
    """
    if pd.isna(text):
        return None

    text = str(text)

    # Key phrases that introduce rationales
    rationale_markers = [
        r'we\s+(?:are\s+)?(?:grant|deny|approv)(?:ing|ed)',
        r'(?:for\s+the\s+following\s+reasons?|because)',
        r'we\s+(?:have\s+)?determined\s+that',
        r'the\s+(?:agency|fda)\s+(?:has\s+)?(?:determined|concluded)',
        r'(?:after\s+)?(?:careful\s+)?(?:review|consideration)',
        r'based\s+on\s+(?:our\s+)?(?:review|analysis)',
    ]

    # Find the first occurrence of any rationale marker
    best_start = None
    best_pattern = None

    for pattern in rationale_markers:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if best_start is None or match.start() < best_start:
                best_start = match.start()
                best_pattern = pattern

    if best_start is not None:
        # Extract from the marker to the next 1000 characters
        start_pos = max(0, best_start - 50)  # Include a bit of context before
        end_pos = min(len(text), best_start + 1000)
        rationale = text[start_pos:end_pos]

        # Clean up
        rationale = re.sub(r'\s+', ' ', rationale)  # Normalize whitespace
        rationale = rationale.strip()

        return rationale

    # If no specific marker found, return first 1000 chars as fallback
    return text[:1000].strip()

print("\nExtracting rationale text from responses...")
final_responses['Rationale_Text'] = final_responses.apply(
    lambda row: extract_rationale_text(row['text'], row['Mined_Response_Type']),
    axis=1
)

# ============================================================================
# CATEGORIZE FDA RESPONSE PATTERNS
# ============================================================================

def categorize_fda_reasoning(text, decision_type):
    """
    Categorize the type of reasoning FDA uses for their decision.
    Different categories for approvals vs denials.
    """
    if pd.isna(text):
        return 'Unknown - No Text'

    text = str(text).lower()

    # APPROVAL PATTERNS
    if decision_type == 'Approved':
        # Check what FDA emphasizes in approval
        if any(phrase in text for phrase in ['bioequivalence', 'bioequivalent', 'be study']):
            return 'APPROVAL: Bioequivalence Demonstrated'
        elif any(phrase in text for phrase in ['safety', 'safe', 'no safety concern']):
            return 'APPROVAL: Safety Established'
        elif any(phrase in text for phrase in ['public health', 'public interest']):
            return 'APPROVAL: Public Health Benefit'
        elif any(phrase in text for phrase in ['evidence', 'data', 'studies support']):
            return 'APPROVAL: Sufficient Evidence'
        elif any(phrase in text for phrase in ['therapeutic equivalence', 'ab-rated']):
            return 'APPROVAL: Therapeutic Equivalence'
        elif any(phrase in text for phrase in ['agree', 'concur', 'merit']):
            return 'APPROVAL: FDA Agrees with Petitioner'
        elif any(phrase in text for phrase in ['labeling', 'label change']):
            return 'APPROVAL: Labeling Change Warranted'
        else:
            return 'APPROVAL: Other/General Approval'

    # DENIAL PATTERNS
    elif decision_type == 'Denied':
        # Evidentiary denials
        if any(phrase in text for phrase in ['insufficient evidence', 'lack of evidence', 'inadequate data', 'no data', 'insufficient data']):
            return 'DENIAL: Insufficient Evidence/Data'

        # Jurisdictional/Authority denials
        elif any(phrase in text for phrase in ['no jurisdiction', 'outside.*scope', 'not.*authority', 'beyond.*authority', 'no statutory authority']):
            return 'DENIAL: Outside FDA Authority'

        # Procedural denials
        elif any(phrase in text for phrase in ['premature', 'pending', 'ongoing review', 'under review']):
            return 'DENIAL: Premature/Pending Other Action'

        # Enforcement discretion
        elif any(phrase in text for phrase in ['enforcement discretion', 'enforcement priorities', 'limited resources']):
            return 'DENIAL: Enforcement Discretion'

        # No public health concern
        elif any(phrase in text for phrase in ['no public health', 'not.*public health concern', 'no safety concern', 'no risk']):
            return 'DENIAL: No Public Health Concern'

        # Disagree with premise
        elif any(phrase in text for phrase in ['disagree', 'not persuaded', 'do not agree', 'unpersuasive']):
            return 'DENIAL: FDA Disagrees with Petition'

        # Already addressed/moot
        elif any(phrase in text for phrase in ['moot', 'already', 'existing', 'current.*adequate']):
            return 'DENIAL: Already Addressed/Moot'

        # Procedural deficiency
        elif any(phrase in text for phrase in ['procedural', 'administrative', 'format', 'submission']):
            return 'DENIAL: Procedural Deficiency'

        # Scientific/technical disagreement
        elif any(phrase in text for phrase in ['scientific', 'technical', 'methodology', 'analysis']):
            return 'DENIAL: Scientific/Technical Disagreement'

        else:
            return 'DENIAL: Other/Unspecified Reason'

    # PARTIAL APPROVAL
    elif decision_type == 'Partially Approved':
        return 'PARTIAL: Some Requests Granted, Others Denied'

    # WITHDRAWN
    elif decision_type == 'Withdrawn':
        return 'WITHDRAWN: Petitioner Withdrew Request'

    else:
        return 'OTHER: Unknown Decision Type'

print("\nCategorizing FDA reasoning patterns...")
final_responses['FDA_Reasoning_Category'] = final_responses.apply(
    lambda row: categorize_fda_reasoning(row['text'], row['Mined_Response_Type']),
    axis=1
)

# ============================================================================
# CREATE FOCUSED DATASET
# ============================================================================

# Select and rename columns for clarity
rationale_dataset = final_responses[[
    'Document ID',
    'Title',
    'Docket ID',
    'Petitioner',
    'FDA Center',
    'Mined_Response_Type',
    'FDA_Reasoning_Category',
    'Rationale_Text',
    'Document Link'
]].copy()

# Rename for clarity
rationale_dataset.columns = [
    'Document_ID',
    'Document_Title',
    'Docket_ID',
    'Petitioner',
    'FDA_Center',
    'Decision',
    'FDA_Reasoning_Category',
    'Rationale_Text',
    'Document_Link'
]

# Sort by decision type then category
rationale_dataset = rationale_dataset.sort_values(['Decision', 'FDA_Reasoning_Category'])

# ============================================================================
# SAVE AND REPORT
# ============================================================================

output_path = '/Users/avani/FDA_Analysis/fda_rationales_dataset.csv'
rationale_dataset.to_csv(output_path, index=False)

print(f"\n✓ Saved: {output_path}")
print(f"  Total documents: {len(rationale_dataset):,}")

# Print distribution
print("\n" + "="*80)
print("FDA REASONING CATEGORY DISTRIBUTION")
print("="*80)

print("\nAPPROVALS:")
approvals = rationale_dataset[rationale_dataset['Decision'] == 'Approved']
for category, count in approvals['FDA_Reasoning_Category'].value_counts().items():
    print(f"  {category:50s}: {count:>4}")

print("\nDENIALS:")
denials = rationale_dataset[rationale_dataset['Decision'] == 'Denied']
for category, count in denials['FDA_Reasoning_Category'].value_counts().items():
    print(f"  {category:50s}: {count:>4}")

print("\nOTHER DECISIONS:")
other = rationale_dataset[~rationale_dataset['Decision'].isin(['Approved', 'Denied'])]
for category, count in other['FDA_Reasoning_Category'].value_counts().items():
    print(f"  {category:50s}: {count:>4}")

# ============================================================================
# CREATE SUMMARY STATISTICS
# ============================================================================

summary_stats = rationale_dataset.groupby(['Decision', 'FDA_Reasoning_Category']).size().reset_index(name='Count')
summary_stats = summary_stats.sort_values(['Decision', 'Count'], ascending=[True, False])

summary_path = '/Users/avani/FDA_Analysis/fda_rationales_summary.csv'
summary_stats.to_csv(summary_path, index=False)
print(f"\n✓ Saved summary: {summary_path}")

# ============================================================================
# SAMPLE RATIONALES FOR REVIEW
# ============================================================================

print("\n" + "="*80)
print("SAMPLE RATIONALES (First 300 chars)")
print("="*80)

# Show 2 examples of each major category
categories_to_sample = [
    'DENIAL: Insufficient Evidence/Data',
    'DENIAL: Premature/Pending Other Action',
    'DENIAL: Outside FDA Authority',
    'DENIAL: No Public Health Concern',
    'APPROVAL: Bioequivalence Demonstrated',
    'APPROVAL: Sufficient Evidence'
]

for category in categories_to_sample:
    samples = rationale_dataset[rationale_dataset['FDA_Reasoning_Category'] == category].head(2)
    if len(samples) > 0:
        print(f"\n{category}")
        print("-" * 80)
        for idx, row in samples.iterrows():
            print(f"\nDoc: {row['Document_ID']}")
            print(f"Petitioner: {row['Petitioner']}")
            rationale_preview = row['Rationale_Text'][:300] if pd.notna(row['Rationale_Text']) else "No text"
            print(f"Rationale: {rationale_preview}...")

print("\n" + "="*80)
print("DATASET COMPLETE")
print("="*80)
print(f"\nMain file: {output_path}")
print(f"Summary: {summary_path}")
print(f"\nColumns: {', '.join(rationale_dataset.columns)}")
print(f"Total rows: {len(rationale_dataset):,}")
