#!/usr/bin/env python3
"""
Enhance FDA Petition Data by Mining Text for Response Types and Calculating Response Times
"""

import pandas as pd
import re
from datetime import datetime
from dateutil import parser
import numpy as np

print("="*80)
print("ENHANCING FDA PETITION DATA")
print("="*80)

# Load data
df = pd.read_csv('/Users/avani/FDA_Analysis/complete_fda_petitions_with_text.csv')
print(f"\nLoaded {len(df):,} documents")

# ============================================================================
# 1. MINE RESPONSE TYPE FROM TEXT
# ============================================================================

print("\n1. Mining Response Types from Text...")
print("-"*80)

def extract_response_type_from_text(text, title, existing_response_type):
    """Extract response type by analyzing text and title"""

    # If we already have a response type, use it
    if pd.notna(existing_response_type) and str(existing_response_type).strip():
        return existing_response_type

    if pd.isna(text) or str(text) == 'nan' or len(str(text)) < 50:
        return None

    text = str(text).lower()
    title = str(title).lower() if pd.notna(title) else ""
    combined = text + " " + title

    # Approval patterns
    approval_patterns = [
        r'petition\s+is\s+granted',
        r'petition\s+is\s+approved',
        r'we\s+are\s+granting',
        r'we\s+grant\s+the\s+petition',
        r'approve\s+the\s+petition',
        r'petition\s+approval',
        r'granted\s+the\s+petition'
    ]

    # Denial patterns
    denial_patterns = [
        r'petition\s+is\s+denied',
        r'petition\s+is\s+rejected',
        r'we\s+are\s+denying',
        r'we\s+deny\s+the\s+petition',
        r'petition\s+denial',
        r'denied\s+the\s+petition',
        r'decline\s+to\s+grant'
    ]

    # Partial approval patterns
    partial_patterns = [
        r'partially\s+grant',
        r'grant\s+in\s+part',
        r'partially\s+approve',
        r'partial\s+approval'
    ]

    # Withdrawal patterns
    withdrawal_patterns = [
        r'petition\s+withdrawn',
        r'petitioner\s+withdrew',
        r'withdrawal\s+of\s+petition',
        r'request\s+to\s+withdraw'
    ]

    # Check patterns in order of specificity
    for pattern in partial_patterns:
        if re.search(pattern, combined):
            return 'Partially Approved'

    for pattern in approval_patterns:
        if re.search(pattern, combined):
            return 'Approved'

    for pattern in denial_patterns:
        if re.search(pattern, combined):
            return 'Denied'

    for pattern in withdrawal_patterns:
        if re.search(pattern, combined):
            return 'Withdrawn'

    # Check title for clear indicators
    if 'approval' in title:
        return 'Approved'
    if 'denial' in title or 'denied' in title:
        return 'Denied'
    if 'withdraw' in title:
        return 'Withdrawn'

    return None

# Apply to all rows
print("  Analyzing text for response types...")
df['Mined_Response_Type'] = df.apply(
    lambda row: extract_response_type_from_text(
        row['text'],
        row['Title'],
        row['Response Type']
    ),
    axis=1
)

# Count improvements
original_response_types = df['Response Type'].notna().sum()
mined_response_types = df['Mined_Response_Type'].notna().sum()
print(f"  Original Response Type entries: {original_response_types:,}")
print(f"  Mined Response Type entries: {mined_response_types:,}")
print(f"  Improvement: +{mined_response_types - original_response_types:,} entries")

# Show distribution
print("\n  Mined Response Type Distribution:")
for rtype, count in df['Mined_Response_Type'].value_counts().head(10).items():
    if pd.notna(rtype):
        print(f"    {rtype:30s}: {count:>5,} ({count/len(df)*100:>5.1f}%)")

# ============================================================================
# 2. EXTRACT DATES FROM TEXT
# ============================================================================

print("\n2. Mining Dates from Text...")
print("-"*80)

def extract_dates_from_text(text):
    """Extract dates from text using various patterns"""
    if pd.isna(text) or str(text) == 'nan':
        return []

    text = str(text)
    dates = []

    # Common date patterns
    date_patterns = [
        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',
        r'\b\d{1,2}-\d{1,2}-\d{4}\b',
        r'\b\d{4}-\d{1,2}-\d{1,2}\b',
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                # Try to parse the date
                parsed_date = parser.parse(match)
                if 1990 <= parsed_date.year <= 2025:  # Reasonable date range
                    dates.append(parsed_date)
            except:
                continue

    return sorted(list(set(dates)))

print("  Extracting dates from text (first 1000 docs for speed)...")
sample_dates = []
for idx, row in df.head(1000).iterrows():
    if idx % 200 == 0:
        print(f"    Processing row {idx}...")
    dates = extract_dates_from_text(row['text'])
    if dates:
        sample_dates.append(len(dates))

if sample_dates:
    print(f"  Average dates found per document: {np.mean(sample_dates):.1f}")
    print(f"  Documents with dates: {len([d for d in sample_dates if d > 0])}/1000")

# ============================================================================
# 3. CALCULATE RESPONSE TIME BY MATCHING PETITIONS WITH RESPONSES
# ============================================================================

print("\n3. Calculating Response Times by Docket...")
print("-"*80)

# Group documents by docket
dockets = df.groupby('Docket ID')

print(f"  Total unique dockets: {df['Docket ID'].nunique():,}")

# For each docket, find petition and response pairs
response_times = []
petition_response_pairs = []

for docket_id, group in dockets:
    # Find petitions
    petitions = group[group['Type of Document (Petition, Interim Response, Final Response)'].isin(['Petition', 'Citizen Petition'])]

    # Find responses
    responses = group[group['Type of Document (Petition, Interim Response, Final Response)'].isin(['Final Response', 'Interim Response'])]

    if len(petitions) > 0 and len(responses) > 0:
        # Try to match by dates if available
        for _, petition in petitions.iterrows():
            petition_date = petition.get('Petition Date')

            for _, response in responses.iterrows():
                response_date = response.get('Response Date')

                # Calculate response time if both dates available
                if pd.notna(petition_date) and pd.notna(response_date):
                    try:
                        p_date = pd.to_datetime(petition_date)
                        r_date = pd.to_datetime(response_date)
                        days_diff = (r_date - p_date).days

                        if 0 <= days_diff <= 3650:  # Between 0 and 10 years
                            response_times.append(days_diff)
                            petition_response_pairs.append({
                                'Docket ID': docket_id,
                                'Petition_Doc': petition['Document ID'],
                                'Response_Doc': response['Document ID'],
                                'Response_Days': days_diff,
                                'Within_180': days_diff <= 180
                            })
                    except:
                        continue

print(f"  Petition-Response pairs with date info: {len(petition_response_pairs)}")

if response_times:
    print(f"\n  Response Time Statistics:")
    print(f"    Mean: {np.mean(response_times):.0f} days")
    print(f"    Median: {np.median(response_times):.0f} days")
    print(f"    Within 180 days: {sum(1 for d in response_times if d <= 180)}/{len(response_times)} ({sum(1 for d in response_times if d <= 180)/len(response_times)*100:.1f}%)")
    print(f"    Over 180 days: {sum(1 for d in response_times if d > 180)}/{len(response_times)} ({sum(1 for d in response_times if d > 180)/len(response_times)*100:.1f}%)")
else:
    print("  Insufficient date data to calculate response times")
    print("  Note: Only 4.1% of petitions and 3.9% of responses have date information")

# ============================================================================
# 4. ADD DOCUMENT SEQUENCE INFO
# ============================================================================

print("\n4. Adding Document Sequence Information...")
print("-"*80)

# For each docket, identify the sequence of documents
def determine_document_role(group):
    """Determine role of each document in docket"""
    # Sort by document ID (which includes sequence number)
    group = group.sort_values('Document ID')

    roles = []
    for idx, row in group.iterrows():
        doc_type = row['Type of Document (Petition, Interim Response, Final Response)']

        if doc_type in ['Petition', 'Citizen Petition']:
            roles.append('Initial Petition')
        elif doc_type == 'Interim Response':
            roles.append('Interim FDA Response')
        elif doc_type == 'Final Response':
            roles.append('Final FDA Response')
        elif 'letter' in str(row['Title']).lower():
            roles.append('Correspondence')
        else:
            roles.append('Other Document')

    return roles

df['Document_Role'] = None
for docket_id, group in dockets:
    roles = determine_document_role(group)
    df.loc[group.index, 'Document_Role'] = roles

print(f"  Added document role information")
print("\n  Document Role Distribution:")
for role, count in df['Document_Role'].value_counts().head(10).items():
    if pd.notna(role):
        print(f"    {role:30s}: {count:>5,}")

# ============================================================================
# 5. SAVE ENHANCED DATA
# ============================================================================

print("\n5. Saving Enhanced Data...")
print("-"*80)

# Save main enhanced file
output_path = '/Users/avani/FDA_Analysis/enhanced_fda_petitions.csv'
df.to_csv(output_path, index=False)
print(f"  ✓ Saved enhanced data to: {output_path}")

# Save petition-response pairs if available
if petition_response_pairs:
    pairs_df = pd.DataFrame(petition_response_pairs)
    pairs_path = '/Users/avani/FDA_Analysis/petition_response_pairs.csv'
    pairs_df.to_csv(pairs_path, index=False)
    print(f"  ✓ Saved petition-response pairs to: {pairs_path}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "="*80)
print("ENHANCEMENT SUMMARY")
print("="*80)

print(f"""
DATA COMPLETENESS IMPROVEMENTS:

1. Response Type:
   Before: {original_response_types:,} ({original_response_types/len(df)*100:.1f}%)
   After:  {mined_response_types:,} ({mined_response_types/len(df)*100:.1f}%)
   Gain:   +{mined_response_types - original_response_types:,} entries

2. Document Roles:
   Added sequence information for all {len(df):,} documents

3. Petition-Response Matching:
   Identified {len(petition_response_pairs)} petition-response pairs with timing data

NEXT STEPS TO FURTHER IMPROVE DATA:

1. Full Date Extraction:
   Run date extraction on ALL documents (not just sample)
   This would enable response time calculation for more dockets

2. OCR for Scanned Documents:
   Process {df['is_scanned'].sum():,} scanned PDFs to extract more text
   This would improve response type mining

3. External Data Linking:
   Link to FDA Orange Book for generic drug approval dates
   Link to Federal Register for additional context

FILES CREATED:
• enhanced_fda_petitions.csv - Main dataset with mined fields
• petition_response_pairs.csv - Petition-response timing pairs (if available)
""")

print("="*80)
print("DONE!")
print("="*80)
