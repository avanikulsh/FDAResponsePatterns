#!/usr/bin/env python3
"""
Analyze FDA's Rationales and Reasoning in Response Documents
Extract and compare how FDA justifies approvals vs denials
"""

import pandas as pd
import re
from collections import Counter
import numpy as np

print("="*80)
print("ANALYZING FDA RATIONALES IN RESPONSE DOCUMENTS")
print("="*80)

# Load data
df = pd.read_csv('/Users/avani/FDA_Analysis/enhanced_fda_petitions.csv')

# Filter to final responses with text
responses = df[
    (df['Type of Document (Petition, Interim Response, Final Response)'] == 'Final Response') &
    (df['Mined_Response_Type'].notna()) &
    (df['text'].notna()) &
    (df['text'].str.len() > 100)
].copy()

print(f"\nAnalyzing {len(responses):,} response documents with text")

# Separate by decision type
approved = responses[responses['Mined_Response_Type'] == 'Approved']
denied = responses[responses['Mined_Response_Type'] == 'Denied']

print(f"  Approved: {len(approved):,}")
print(f"  Denied: {len(denied):,}")

# ============================================================================
# 1. EXTRACT COMMON JUSTIFICATION PHRASES
# ============================================================================

print("\n" + "="*80)
print("PATTERN 1: FDA'S JUSTIFICATION LANGUAGE")
print("="*80)

def extract_justification_phrases(text_series, decision_type):
    """Extract common phrases FDA uses to justify decisions"""

    # Common rationale patterns
    approval_patterns = [
        r'we\s+(?:are\s+)?grant(?:ing|ed)?\s+(?:the\s+)?(?:petition|request)?\s+because\s+(.{0,200})',
        r'we\s+(?:have\s+)?determined\s+that\s+(.{0,200})',
        r'we\s+(?:agree|concur)\s+(?:that|with)\s+(.{0,200})',
        r'the\s+(?:agency|fda)\s+has\s+determined\s+that\s+(.{0,200})',
        r'(?:for\s+the\s+following\s+reasons?|because):\s+(.{0,200})',
    ]

    denial_patterns = [
        r'we\s+(?:are\s+)?deny(?:ing|ied)?\s+(?:the\s+)?(?:petition|request)?\s+because\s+(.{0,200})',
        r'we\s+(?:have\s+)?determined\s+that\s+(.{0,200})',
        r'we\s+disagree\s+(?:that|with)\s+(.{0,200})',
        r'(?:you\s+)?(?:have\s+)?not\s+(?:provided|demonstrated|shown)\s+(.{0,200})',
        r'(?:insufficient|inadequate|lack\s+of)\s+(.{0,200})',
        r'the\s+(?:petition|request)\s+(?:fails|does\s+not)\s+(.{0,200})',
    ]

    patterns = approval_patterns if decision_type == 'Approved' else denial_patterns

    found_phrases = []
    for text in text_series:
        if pd.isna(text):
            continue
        text = str(text).lower()

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean up the extracted phrase
                phrase = match.strip()[:150]  # First 150 chars
                if len(phrase) > 20:  # Skip very short matches
                    found_phrases.append(phrase)

    return found_phrases

print("\nExtracting approval justifications...")
approval_phrases = extract_justification_phrases(approved['text'], 'Approved')
print(f"Found {len(approval_phrases)} justification excerpts in approved responses")

print("\nExtracting denial justifications...")
denial_phrases = extract_justification_phrases(denied['text'], 'Denied')
print(f"Found {len(denial_phrases)} justification excerpts in denied responses")

# ============================================================================
# 2. COMMON KEYWORDS IN RATIONALES
# ============================================================================

print("\n" + "="*80)
print("PATTERN 2: KEY REASONING TERMS")
print("="*80)

def extract_keywords(text_series):
    """Extract important substantive keywords from rationales"""
    keywords = []

    # Important regulatory/scientific terms
    key_terms = [
        'safety', 'efficacy', 'evidence', 'data', 'study', 'studies',
        'risk', 'benefit', 'public health', 'scientific', 'clinical',
        'regulation', 'statutory', 'authority', 'jurisdiction',
        'insufficient', 'adequate', 'appropriate', 'necessary',
        'bioequivalence', 'therapeutic', 'generic', 'labeling',
        'adverse', 'compliance', 'violation', 'standard'
    ]

    for text in text_series:
        if pd.isna(text):
            continue
        text_lower = str(text).lower()

        for term in key_terms:
            if term in text_lower:
                keywords.append(term)

    return Counter(keywords)

approved_keywords = extract_keywords(approved['text'])
denied_keywords = extract_keywords(denied['text'])

print("\nTop 15 terms in APPROVED responses:")
for term, count in approved_keywords.most_common(15):
    pct = (count / len(approved)) * 100
    print(f"  {term:20s}: {count:>4} mentions ({pct:>5.1f}% of approved responses)")

print("\nTop 15 terms in DENIED responses:")
for term, count in denied_keywords.most_common(15):
    pct = (count / len(denied)) * 100
    print(f"  {term:>20s}: {count:>4} mentions ({pct:>5.1f}% of denied responses)")

# ============================================================================
# 3. ANALYZE SUBSTANTIVENESS OF RATIONALES
# ============================================================================

print("\n" + "="*80)
print("PATTERN 3: SUBSTANTIVENESS OF FDA REASONING")
print("="*80)

def analyze_rationale_depth(text):
    """Estimate how detailed/substantive the rationale is"""
    if pd.isna(text) or len(str(text)) < 100:
        return 'No rationale'

    text_lower = str(text).lower()

    # Count substantive elements
    evidence_mentions = len(re.findall(r'(data|evidence|study|studies|research|analysis)', text_lower))
    legal_citations = len(re.findall(r'(section\s+\d+|21\s+cfr|usc|statute)', text_lower))
    scientific_terms = len(re.findall(r'(safety|efficacy|bioequivalence|pharmacokinetic|clinical)', text_lower))

    total_indicators = evidence_mentions + legal_citations + scientific_terms

    if total_indicators >= 10:
        return 'Highly detailed'
    elif total_indicators >= 5:
        return 'Moderately detailed'
    elif total_indicators >= 2:
        return 'Brief'
    else:
        return 'Minimal'

approved['Rationale_Depth'] = approved['text'].apply(analyze_rationale_depth)
denied['Rationale_Depth'] = denied['text'].apply(analyze_rationale_depth)

print("\nRationale substantiveness in APPROVED responses:")
for depth, count in approved['Rationale_Depth'].value_counts().items():
    print(f"  {depth:20s}: {count:>4} ({count/len(approved)*100:>5.1f}%)")

print("\nRationale substantiveness in DENIED responses:")
for depth, count in denied['Rationale_Depth'].value_counts().items():
    print(f"  {depth:20s}: {count:>4} ({count/len(denied)*100:>5.1f}%)")

# ============================================================================
# 4. SPECIFIC DENIAL REASONS
# ============================================================================

print("\n" + "="*80)
print("PATTERN 4: SPECIFIC REASONS FOR DENIAL")
print("="*80)

def categorize_denial_reason(text):
    """Categorize the primary reason for denial"""
    if pd.isna(text):
        return 'Unknown'

    text = str(text).lower()

    # Look for specific denial reasons
    if 'insufficient evidence' in text or 'lack of evidence' in text or 'inadequate data' in text:
        return 'Insufficient evidence/data'
    elif 'no jurisdiction' in text or 'outside.*scope' in text or 'not.*authority' in text:
        return 'Outside FDA authority'
    elif 'public health' in text and ('no.*risk' in text or 'not.*warrant' in text):
        return 'No public health concern'
    elif 'premature' in text or 'pending' in text:
        return 'Premature/Pending other action'
    elif 'enforcement' in text and 'discretion' in text:
        return 'Enforcement discretion'
    elif 'moot' in text or 'withdrawn' in text:
        return 'Moot/Withdrawn'
    elif 'procedural' in text or 'administrative' in text:
        return 'Procedural issue'
    else:
        return 'Other/Unspecified'

denied['Denial_Reason'] = denied['text'].apply(categorize_denial_reason)

print("\nCategorized denial reasons:")
for reason, count in denied['Denial_Reason'].value_counts().items():
    print(f"  {reason:35s}: {count:>4} ({count/len(denied)*100:>5.1f}%)")

# ============================================================================
# 5. COMPARE RATIONALES BY PETITIONER TYPE
# ============================================================================

print("\n" + "="*80)
print("PATTERN 5: DO RATIONALES DIFFER BY PETITIONER TYPE?")
print("="*80)

# Categorize petitioners (reuse function from previous script)
def categorize_petitioner(petitioner):
    if pd.isna(petitioner):
        return 'Unknown'
    petitioner = str(petitioner).lower()

    public_keywords = ['public citizen', 'consumer', 'advocacy']
    consultant_keywords = ['consult', 'lachman']
    industry_keywords = ['pharma', 'inc', 'corp', 'llc']

    if any(k in petitioner for k in public_keywords):
        return 'Public Interest'
    elif any(k in petitioner for k in consultant_keywords):
        return 'Consultant'
    elif any(k in petitioner for k in industry_keywords):
        return 'Industry'
    else:
        return 'Other'

denied['Petitioner_Category'] = denied['Petitioner'].apply(categorize_petitioner)

print("\nDenial reasons by petitioner type:")
denial_by_type = denied.groupby(['Petitioner_Category', 'Denial_Reason']).size().unstack(fill_value=0)
print(denial_by_type)

print("\nRationale depth for DENIED petitions by petitioner category:")
depth_by_type = denied.groupby(['Petitioner_Category', 'Rationale_Depth']).size().unstack(fill_value=0)
print(depth_by_type)

# ============================================================================
# 6. SAMPLE ACTUAL RATIONALES
# ============================================================================

print("\n" + "="*80)
print("PATTERN 6: SAMPLE ACTUAL FDA RATIONALE EXCERPTS")
print("="*80)

print("\n--- SAMPLE APPROVALS ---")
for idx, row in approved.sample(min(3, len(approved))).iterrows():
    print(f"\nDocument: {row['Document ID']}")
    print(f"Petitioner: {row['Petitioner']}")
    text = str(row['text'])

    # Extract the section with justification
    grant_match = re.search(r'(we\s+(?:are\s+)?grant.{0,400})', text, re.IGNORECASE)
    if grant_match:
        excerpt = grant_match.group(1).replace('\n', ' ')[:300]
        print(f"Excerpt: ...{excerpt}...")

print("\n--- SAMPLE DENIALS ---")
for idx, row in denied.sample(min(3, len(denied))).iterrows():
    print(f"\nDocument: {row['Document ID']}")
    print(f"Petitioner: {row['Petitioner']}")
    print(f"Denial Reason: {row['Denial_Reason']}")
    text = str(row['text'])

    # Extract the section with justification
    deny_match = re.search(r'(we\s+(?:are\s+)?deny.{0,400})', text, re.IGNORECASE)
    if deny_match:
        excerpt = deny_match.group(1).replace('\n', ' ')[:300]
        print(f"Excerpt: ...{excerpt}...")

# ============================================================================
# 7. SAVE RESULTS
# ============================================================================

print("\n" + "="*80)
print("SAVING ANALYSIS")
print("="*80)

# Save rationale analysis
rationale_summary = {
    'Response_Type': ['Approved', 'Denied'],
    'Total_Responses': [len(approved), len(denied)],
    'Highly_Detailed': [
        (approved['Rationale_Depth'] == 'Highly detailed').sum(),
        (denied['Rationale_Depth'] == 'Highly detailed').sum()
    ],
    'Minimal': [
        (approved['Rationale_Depth'] == 'Minimal').sum(),
        (denied['Rationale_Depth'] == 'Minimal').sum()
    ]
}

summary_df = pd.DataFrame(rationale_summary)
summary_df.to_csv('/Users/avani/FDA_Analysis/rationale_analysis_summary.csv', index=False)
print("✓ Saved: rationale_analysis_summary.csv")

# Save denial reasons
denied[['Document ID', 'Petitioner', 'Petitioner_Category', 'Denial_Reason', 'Rationale_Depth']].to_csv(
    '/Users/avani/FDA_Analysis/denial_reasons_detailed.csv', index=False
)
print("✓ Saved: denial_reasons_detailed.csv")

# ============================================================================
# SUMMARY REPORT
# ============================================================================

print("\n" + "="*80)
print("KEY FINDINGS: HOW FDA RATIONALIZES ITS DECISIONS")
print("="*80)

report = f"""
1. SUBSTANTIVENESS OF RATIONALES:
   Approved responses:
     • Highly detailed: {(approved['Rationale_Depth'] == 'Highly detailed').sum()} ({(approved['Rationale_Depth'] == 'Highly detailed').sum()/len(approved)*100:.1f}%)
     • Minimal: {(approved['Rationale_Depth'] == 'Minimal').sum()} ({(approved['Rationale_Depth'] == 'Minimal').sum()/len(approved)*100:.1f}%)

   Denied responses:
     • Highly detailed: {(denied['Rationale_Depth'] == 'Highly detailed').sum()} ({(denied['Rationale_Depth'] == 'Highly detailed').sum()/len(denied)*100:.1f}%)
     • Minimal: {(denied['Rationale_Depth'] == 'Minimal').sum()} ({(denied['Rationale_Depth'] == 'Minimal').sum()/len(denied)*100:.1f}%)

2. MOST COMMON DENIAL REASONS:
{denied['Denial_Reason'].value_counts().head().to_string()}

3. KEY TERMS IN FDA REASONING:
   Approvals emphasize: {', '.join([k for k, v in approved_keywords.most_common(5)])}
   Denials emphasize: {', '.join([k for k, v in denied_keywords.most_common(5)])}

4. DOES RATIONALE QUALITY VARY BY PETITIONER?
   Analyzing whether FDA provides more detailed justifications to certain petitioners...

OVERALL CONCLUSION:
FDA's rationales reveal how they justify decisions. Analysis shows whether
FDA provides substantive scientific reasoning vs procedural dismissals, and
whether rationale depth correlates with petitioner type.
"""

print(report)

with open('/Users/avani/FDA_Analysis/rationale_analysis_report.txt', 'w') as f:
    f.write("FDA RATIONALE ANALYSIS\n")
    f.write("="*80 + "\n\n")
    f.write(report)

print("\n✓ Saved: rationale_analysis_report.txt")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
