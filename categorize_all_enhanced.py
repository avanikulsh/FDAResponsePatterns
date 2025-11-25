#!/usr/bin/env python3
"""
Enhanced FDA Reasoning Categorization
Informed by TF-IDF and N-gram analysis - data-driven categories
"""

import pandas as pd
import re

print("="*80)
print("ENHANCED REASONING CATEGORIZATION")
print("Data-driven categories based on computational analysis")
print("="*80)

# Load rationale dataset
df = pd.read_csv('/Users/avani/FDA_Analysis/fda_rationales_dataset.csv')

# Filter to documents with rationale text
df_to_categorize = df[df['Rationale_Text'].notna()].copy()
df_to_categorize = df_to_categorize[df_to_categorize['Rationale_Text'].str.len() > 50].copy()

print(f"\nDocuments to categorize: {len(df_to_categorize)}")

# ============================================================================
# ENHANCED CATEGORIZATION (Data-Driven from TF-IDF Analysis)
# ============================================================================

def categorize_reasoning_enhanced(text, decision):
    """
    Enhanced categorization using distinctive phrases identified by TF-IDF
    and n-gram analysis. More sophisticated than simple keywords.
    """
    if pd.isna(text):
        return "Unknown - No Text", "low", []

    text_lower = text.lower()

    # Track evidence for each category
    evidence = {}

    # ============================================================================
    # APPROVAL CATEGORIES (Based on TF-IDF distinctive phrases)
    # ============================================================================

    if decision == "Approved":

        # Bioequivalence - distinctive phrases from TF-IDF
        bio_phrases = [
            'bioequivalent', 'bioequivalence', 'be study', 'therapeutic equivalence',
            'listed drug', 'reference listed drug', 'proposed drug product',
            'ab-rated', 'anda', 'orange book', 'rld'
        ]
        bio_score = sum(1 for phrase in bio_phrases if phrase in text_lower)
        evidence["Bioequivalence/Therapeutic Equivalence"] = bio_score

        # Safety - from TF-IDF "safety effectiveness" is distinctive
        safety_phrases = [
            'safety', 'safe', 'no safety concern', 'safety profile',
            'safety effectiveness', 'adverse events', 'toxicity'
        ]
        safety_score = sum(1 for phrase in safety_phrases if phrase in text_lower)
        evidence["Safety Established"] = safety_score

        # Evidence-based - data, studies, etc
        evidence_phrases = [
            'data support', 'evidence', 'studies', 'demonstrated',
            'adequate information', 'sufficient data', 'clinical trials'
        ]
        evidence_score = sum(1 for phrase in evidence_phrases if phrase in text_lower)
        evidence["Sufficient Evidence"] = evidence_score

        # Public health
        public_phrases = [
            'public health', 'public interest', 'benefit', 'access',
            'availability'
        ]
        public_score = sum(1 for phrase in public_phrases if phrase in text_lower)
        evidence["Public Health Benefit"] = public_score

        # FDA agrees
        agree_phrases = [
            'agree', 'granted', 'merit', 'warrant', 'appropriate',
            'concur', 'petition granted'
        ]
        agree_score = sum(1 for phrase in agree_phrases if phrase in text_lower)
        evidence["FDA Concurrence"] = agree_score

        # Get category with most evidence
        if max(evidence.values()) > 0:
            category = max(evidence, key=evidence.get)
            confidence = "high" if evidence[category] >= 2 else "medium"
            key_phrases = [p for p in bio_phrases + safety_phrases + evidence_phrases + public_phrases + agree_phrases if p in text_lower]
            return category, confidence, key_phrases[:3]
        else:
            return "Other Approval Reason", "low", []

    # ============================================================================
    # DENIAL CATEGORIES (Based on TF-IDF and contrastive analysis)
    # ============================================================================

    elif decision == "Denied":

        # Procedural - Premature/Pending (from n-gram analysis)
        premature_phrases = [
            'premature', 'pending', 'ongoing', 'under review', 'not yet',
            'before', 'prior to', 'awaiting'
        ]
        premature_score = sum(1 for phrase in premature_phrases if phrase in text_lower)
        evidence["Procedural - Premature/Pending"] = premature_score

        # Procedural - Administrative (21 CFR 10 is distinctive to denials)
        admin_phrases = [
            'procedural', 'administrative', '21 cfr 10', 'cfr 10',
            'regulation', 'format', 'submission', 'compliance'
        ]
        admin_score = sum(1 for phrase in admin_phrases if phrase in text_lower)
        evidence["Procedural - Administrative Deficiency"] = admin_score

        # Procedural - Already Addressed (from n-grams)
        moot_phrases = [
            'moot', 'already', 'existing', 'previously', 'current',
            'adequate', 'addressed'
        ]
        moot_score = sum(1 for phrase in moot_phrases if phrase in text_lower)
        evidence["Procedural - Already Addressed/Moot"] = moot_score

        # Substantive - Insufficient Evidence
        insufficient_phrases = [
            'insufficient', 'lack', 'inadequate', 'no evidence',
            'no data', 'insufficient evidence', 'inadequate data',
            'lack of evidence', 'lack of data'
        ]
        insufficient_score = sum(1 for phrase in insufficient_phrases if phrase in text_lower)
        evidence["Substantive - Insufficient Evidence"] = insufficient_score

        # Substantive - FDA Disagrees
        disagree_phrases = [
            'disagree', 'not persuaded', 'unpersuasive', 'do not agree',
            'not convinced', 'not support', 'reject'
        ]
        disagree_score = sum(1 for phrase in disagree_phrases if phrase in text_lower)
        evidence["Substantive - FDA Disagrees"] = disagree_score

        # Substantive - No Public Health Concern
        no_concern_phrases = [
            'no public health', 'no safety concern', 'no risk',
            'not pose', 'no evidence of harm'
        ]
        no_concern_score = sum(1 for phrase in no_concern_phrases if phrase in text_lower)
        evidence["Substantive - No Public Health Concern"] = no_concern_score

        # Substantive - Outside Authority
        authority_phrases = [
            'no authority', 'outside', 'jurisdiction', 'scope',
            'not appropriate for', 'beyond'
        ]
        authority_score = sum(1 for phrase in authority_phrases if phrase in text_lower)
        evidence["Substantive - Outside FDA Authority"] = authority_score

        # Enforcement Discretion
        enforcement_phrases = [
            'enforcement discretion', 'enforcement priorities',
            'limited resources', 'priorities'
        ]
        enforcement_score = sum(1 for phrase in enforcement_phrases if phrase in text_lower)
        evidence["Enforcement Discretion"] = enforcement_score

        # Get category with most evidence
        if max(evidence.values()) > 0:
            category = max(evidence, key=evidence.get)
            confidence = "high" if evidence[category] >= 2 else "medium"

            # Get key phrases
            all_phrases = (premature_phrases + admin_phrases + moot_phrases +
                          insufficient_phrases + disagree_phrases + no_concern_phrases +
                          authority_phrases + enforcement_phrases)
            key_phrases = [p for p in all_phrases if p in text_lower]

            return category, confidence, key_phrases[:3]
        else:
            return "Other Denial Reason", "low", []

    else:
        return "Other Decision Type", "low", []

# ============================================================================
# CATEGORIZE ALL DOCUMENTS
# ============================================================================

print("\n" + "="*80)
print("CATEGORIZING ALL DOCUMENTS")
print("="*80)

results = []

for idx, row in df_to_categorize.iterrows():
    if (idx + 1) % 100 == 0:
        print(f"  Processed {idx + 1}/{len(df_to_categorize)} documents...")

    category, confidence, key_phrases = categorize_reasoning_enhanced(
        row['Rationale_Text'],
        row['Decision']
    )

    results.append({
        'Document_ID': row['Document_ID'],
        'Docket_ID': row['Docket_ID'],
        'Document_Title': row['Document_Title'],
        'Petitioner': row['Petitioner'],
        'FDA_Center': row['FDA_Center'],
        'Decision': row['Decision'],
        'Enhanced_Category': category,
        'Confidence': confidence,
        'Key_Phrases': ', '.join(key_phrases[:5]) if key_phrases else '',
        'Rationale_Text': row['Rationale_Text'],
        'Document_Link': row['Document_Link']
    })

results_df = pd.DataFrame(results)

# ============================================================================
# SAVE RESULTS
# ============================================================================

output_path = '/Users/avani/FDA_Analysis/fda_rationales_enhanced_categories.csv'
results_df.to_csv(output_path, index=False)

print(f"\n✓ Saved: {output_path}")
print(f"  Total documents: {len(results_df)}")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print("\n" + "="*80)
print("CATEGORIZATION RESULTS")
print("="*80)

print("\nAPPROVAL CATEGORIES:")
approval_results = results_df[results_df['Decision'] == 'Approved']
for category, count in approval_results['Enhanced_Category'].value_counts().items():
    pct = count / len(approval_results) * 100
    print(f"  {category:50s}: {count:>4} ({pct:>5.1f}%)")

print(f"\nTotal approvals: {len(approval_results)}")

print("\n" + "-"*80)
print("DENIAL CATEGORIES:")
denial_results = results_df[results_df['Decision'] == 'Denied']
for category, count in denial_results['Enhanced_Category'].value_counts().items():
    pct = count / len(denial_results) * 100
    print(f"  {category:50s}: {count:>4} ({pct:>5.1f}%)")

print(f"\nTotal denials: {len(denial_results)}")

# Procedural vs Substantive breakdown
procedural_categories = [
    'Procedural - Premature/Pending',
    'Procedural - Administrative Deficiency',
    'Procedural - Already Addressed/Moot',
    'Enforcement Discretion'
]

procedural_count = len(denial_results[denial_results['Enhanced_Category'].isin(procedural_categories)])
substantive_count = len(denial_results[~denial_results['Enhanced_Category'].isin(procedural_categories + ['Other Denial Reason'])])
other_count = len(denial_results[denial_results['Enhanced_Category'] == 'Other Denial Reason'])

print("\n" + "-"*80)
print("PROCEDURAL vs SUBSTANTIVE BREAKDOWN (Denials Only):")
print(f"  Procedural Dismissals: {procedural_count:>4} ({procedural_count/len(denial_results)*100:>5.1f}%)")
print(f"  Substantive Decisions: {substantive_count:>4} ({substantive_count/len(denial_results)*100:>5.1f}%)")
print(f"  Other/Unclassified:    {other_count:>4} ({other_count/len(denial_results)*100:>5.1f}%)")

# Confidence distribution
print("\n" + "-"*80)
print("CONFIDENCE DISTRIBUTION:")
for conf, count in results_df['Confidence'].value_counts().items():
    pct = count / len(results_df) * 100
    print(f"  {conf:10s}: {count:>4} ({pct:>5.1f}%)")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print("\nNext step: Manually code the validation sample (90 documents)")
print("File: validation_sample_for_manual_coding.csv")
print("\nThen calculate agreement between this enhanced categorization")
print("and your manual coding to establish validity.")
