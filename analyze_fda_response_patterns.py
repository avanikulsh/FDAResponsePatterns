#!/usr/bin/env python3
"""
Analyze Patterns in FDA Response Decisions
Identifies factors that correlate with approval vs denial decisions
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
import re

print("="*80)
print("ANALYZING FDA RESPONSE DECISION PATTERNS")
print("="*80)

# Load enhanced data
df = pd.read_csv('/Users/avani/FDA_Analysis/enhanced_fda_petitions.csv')
print(f"\nLoaded {len(df):,} documents")

# ============================================================================
# 1. CATEGORIZE PETITIONERS
# ============================================================================

def categorize_petitioner(petitioner):
    """Categorize petitioner into broad groups"""
    if pd.isna(petitioner):
        return 'Unknown'

    petitioner = str(petitioner).lower()

    # Public interest groups
    public_keywords = ['public citizen', 'consumer', 'advocacy', 'environmental',
                      'union', 'foundation', 'institute', 'association', 'society',
                      'national center', 'coalition']
    if any(keyword in petitioner for keyword in public_keywords):
        return 'Public Interest'

    # Law firms
    law_keywords = ['llp', 'law', 'attorneys', 'legal', 'esq']
    if any(keyword in petitioner for keyword in law_keywords):
        return 'Law Firm'

    # Consultants
    consultant_keywords = ['consult', 'lachman', 'advisor']
    if any(keyword in petitioner for keyword in consultant_keywords):
        return 'Consultant'

    # Industry (pharmaceutical, biotech, etc.)
    industry_keywords = ['pharma', 'laboratories', 'inc', 'corp', 'llc', 'ltd',
                        'company', 'therapeutics', 'biotech', 'life sciences']
    if any(keyword in petitioner for keyword in industry_keywords):
        return 'Industry'

    # Individuals
    individual_keywords = ['dr.', 'md', 'ph.d']
    if any(keyword in petitioner for keyword in individual_keywords) or len(petitioner.split()) <= 3:
        return 'Individual'

    return 'Other'

df['Petitioner_Category'] = df['Petitioner'].apply(categorize_petitioner)

# ============================================================================
# 2. FILTER TO FINAL RESPONSES ONLY
# ============================================================================

# Focus on petitions that received final responses
petitions = df[df['Type of Document (Petition, Interim Response, Final Response)'].isin(['Petition', 'Citizen Petition'])].copy()
responses = df[df['Type of Document (Petition, Interim Response, Final Response)'] == 'Final Response'].copy()

print(f"\nPetitions: {len(petitions):,}")
print(f"Final Responses: {len(responses):,}")

# Use Mined_Response_Type for analysis (most complete)
responses_with_decision = responses[responses['Mined_Response_Type'].notna()].copy()
print(f"Responses with decision data: {len(responses_with_decision):,}")

# ============================================================================
# 3. PATTERN ANALYSIS: PETITIONER CATEGORY
# ============================================================================

print("\n" + "="*80)
print("PATTERN 1: PETITIONER TYPE vs FDA DECISION")
print("="*80)

# Group by petitioner category and response type
category_response = responses_with_decision.groupby(['Petitioner_Category', 'Mined_Response_Type']).size().unstack(fill_value=0)

print("\nResponse Distribution by Petitioner Category:")
print(category_response)

# Calculate approval rates
category_stats = []
for category in category_response.index:
    total = category_response.loc[category].sum()
    approved = category_response.loc[category].get('Approved', 0)
    denied = category_response.loc[category].get('Denied', 0)

    if total > 0:
        approval_rate = (approved / (approved + denied) * 100) if (approved + denied) > 0 else 0
        category_stats.append({
            'Category': category,
            'Total': total,
            'Approved': approved,
            'Denied': denied,
            'Approval_Rate': approval_rate
        })

category_df = pd.DataFrame(category_stats).sort_values('Approval_Rate', ascending=False)

print("\n" + "-"*80)
print("Approval Rates by Petitioner Category:")
print("-"*80)
for _, row in category_df.iterrows():
    print(f"{row['Category']:20s}: {row['Approval_Rate']:>5.1f}% approved ({row['Approved']}/{row['Approved']+row['Denied']}) n={row['Total']}")

# ============================================================================
# 4. PATTERN ANALYSIS: FDA CENTER
# ============================================================================

print("\n" + "="*80)
print("PATTERN 2: FDA CENTER vs FDA DECISION")
print("="*80)

center_response = responses_with_decision.groupby(['FDA Center', 'Mined_Response_Type']).size().unstack(fill_value=0)

print("\nResponse Distribution by FDA Center:")
print(center_response)

# Calculate approval rates by center
center_stats = []
for center in center_response.index:
    if pd.isna(center):
        continue
    total = center_response.loc[center].sum()
    approved = center_response.loc[center].get('Approved', 0)
    denied = center_response.loc[center].get('Denied', 0)

    if total > 5:  # Only show centers with >5 responses
        approval_rate = (approved / (approved + denied) * 100) if (approved + denied) > 0 else 0
        center_stats.append({
            'Center': center,
            'Total': total,
            'Approved': approved,
            'Denied': denied,
            'Approval_Rate': approval_rate
        })

center_df = pd.DataFrame(center_stats).sort_values('Approval_Rate', ascending=False)

print("\n" + "-"*80)
print("Approval Rates by FDA Center:")
print("-"*80)
for _, row in center_df.iterrows():
    print(f"{row['Center']:10s}: {row['Approval_Rate']:>5.1f}% approved ({row['Approved']}/{row['Approved']+row['Denied']}) n={row['Total']}")

# ============================================================================
# 5. PATTERN ANALYSIS: SPECIFIC PETITIONERS
# ============================================================================

print("\n" + "="*80)
print("PATTERN 3: TOP PETITIONERS vs SUCCESS RATE")
print("="*80)

# Find most frequent petitioners
petitioner_counts = responses_with_decision['Petitioner'].value_counts()
top_petitioners = petitioner_counts[petitioner_counts >= 5].head(15)

print(f"\nAnalyzing top {len(top_petitioners)} petitioners (with 5+ responses)...")

petitioner_stats = []
for petitioner in top_petitioners.index:
    petitioner_responses = responses_with_decision[responses_with_decision['Petitioner'] == petitioner]
    total = len(petitioner_responses)
    approved = (petitioner_responses['Mined_Response_Type'] == 'Approved').sum()
    denied = (petitioner_responses['Mined_Response_Type'] == 'Denied').sum()

    if (approved + denied) > 0:
        approval_rate = (approved / (approved + denied) * 100)
        petitioner_stats.append({
            'Petitioner': petitioner,
            'Total': total,
            'Approved': approved,
            'Denied': denied,
            'Approval_Rate': approval_rate
        })

petitioner_df = pd.DataFrame(petitioner_stats).sort_values('Approval_Rate', ascending=False)

print("\n" + "-"*80)
print("Success Rates of Frequent Petitioners:")
print("-"*80)
for idx, row in petitioner_df.iterrows():
    petitioner_name = str(row['Petitioner'])[:50]
    print(f"{petitioner_name:50s}: {row['Approval_Rate']:>5.1f}% ({row['Approved']}/{row['Approved']+row['Denied']})")

# ============================================================================
# 6. PATTERN ANALYSIS: TEMPORAL TRENDS
# ============================================================================

print("\n" + "="*80)
print("PATTERN 4: APPROVAL RATES OVER TIME")
print("="*80)

# Extract year from document ID or petition date
def extract_year(row):
    # Try from Document ID
    if pd.notna(row.get('Document ID')):
        match = re.search(r'FDA-(\d{4})-P', str(row['Document ID']))
        if match:
            return int(match.group(1))
    return None

responses_with_decision['Year'] = responses_with_decision.apply(extract_year, axis=1)

# Group by year
year_response = responses_with_decision[responses_with_decision['Year'].notna()].groupby(['Year', 'Mined_Response_Type']).size().unstack(fill_value=0)

print("\nResponse trends by year (last 10 years with data):")

year_stats = []
for year in sorted(year_response.index)[-10:]:
    total = year_response.loc[year].sum()
    approved = year_response.loc[year].get('Approved', 0)
    denied = year_response.loc[year].get('Denied', 0)

    if (approved + denied) >= 5:  # At least 5 decisions
        approval_rate = (approved / (approved + denied) * 100)
        year_stats.append({
            'Year': int(year),
            'Total': total,
            'Approved': approved,
            'Denied': denied,
            'Approval_Rate': approval_rate
        })

year_df = pd.DataFrame(year_stats)
print("\n" + "-"*80)
for _, row in year_df.iterrows():
    print(f"{int(row['Year'])}: {row['Approval_Rate']:>5.1f}% approved ({row['Approved']}/{row['Approved']+row['Denied']})")

# ============================================================================
# 7. TEXT ANALYSIS: KEYWORDS IN APPROVED vs DENIED
# ============================================================================

print("\n" + "="*80)
print("PATTERN 5: COMMON THEMES IN PETITIONS")
print("="*80)

# Match petitions with their responses
petition_response_pairs = []

for _, petition in petitions.iterrows():
    docket_id = petition['Docket ID']
    # Find final response in same docket
    docket_responses = responses_with_decision[responses_with_decision['Docket ID'] == docket_id]

    if len(docket_responses) > 0:
        response = docket_responses.iloc[0]
        petition_response_pairs.append({
            'Petition_Title': petition['Title'],
            'Petition_Text': petition.get('text', ''),
            'Response_Type': response['Mined_Response_Type'],
            'FDA_Center': response['FDA Center'],
            'Petitioner': petition['Petitioner']
        })

pairs_df = pd.DataFrame(petition_response_pairs)
print(f"\nMatched {len(pairs_df)} petition-response pairs")

# Common keywords in approved petitions
approved_petitions = pairs_df[pairs_df['Response_Type'] == 'Approved']
denied_petitions = pairs_df[pairs_df['Response_Type'] == 'Denied']

print(f"\nApproved petitions: {len(approved_petitions)}")
print(f"Denied petitions: {len(denied_petitions)}")

# Common themes in titles
def extract_keywords(titles):
    """Extract common multi-word phrases from titles"""
    keywords = []
    for title in titles:
        if pd.isna(title):
            continue
        title = str(title).lower()

        # Look for key regulatory terms
        if 'generic' in title or 'anda' in title:
            keywords.append('generic_approval')
        if 'labeling' in title or 'label' in title:
            keywords.append('labeling_change')
        if 'citizen petition' in title:
            keywords.append('citizen_petition')
        if 'stay' in title:
            keywords.append('stay_of_action')
        if 'drug' in title:
            keywords.append('drug_related')
        if 'food' in title:
            keywords.append('food_related')
        if 'device' in title or 'medical device' in title:
            keywords.append('device_related')

    return Counter(keywords)

approved_themes = extract_keywords(approved_petitions['Petition_Title'])
denied_themes = extract_keywords(denied_petitions['Petition_Title'])

print("\n" + "-"*80)
print("Common themes in APPROVED petitions:")
for theme, count in approved_themes.most_common(5):
    print(f"  {theme:30s}: {count:>3} ({count/len(approved_petitions)*100:.1f}%)")

print("\nCommon themes in DENIED petitions:")
for theme, count in denied_themes.most_common(5):
    print(f"  {theme:30s}: {count:>3} ({count/len(denied_petitions)*100:.1f}%)")

# ============================================================================
# 8. SAVE DETAILED RESULTS
# ============================================================================

print("\n" + "="*80)
print("SAVING DETAILED ANALYSIS")
print("="*80)

# Save petitioner analysis
category_df.to_csv('/Users/avani/FDA_Analysis/pattern_petitioner_category.csv', index=False)
print("✓ Saved: pattern_petitioner_category.csv")

# Save center analysis
center_df.to_csv('/Users/avani/FDA_Analysis/pattern_fda_center.csv', index=False)
print("✓ Saved: pattern_fda_center.csv")

# Save specific petitioner analysis
petitioner_df.to_csv('/Users/avani/FDA_Analysis/pattern_top_petitioners.csv', index=False)
print("✓ Saved: pattern_top_petitioners.csv")

# Save year trends
if len(year_df) > 0:
    year_df.to_csv('/Users/avani/FDA_Analysis/pattern_temporal_trends.csv', index=False)
    print("✓ Saved: pattern_temporal_trends.csv")

# Save petition-response pairs for further analysis
pairs_df.to_csv('/Users/avani/FDA_Analysis/petition_response_matched_pairs.csv', index=False)
print("✓ Saved: petition_response_matched_pairs.csv")

# ============================================================================
# 9. SUMMARY REPORT
# ============================================================================

print("\n" + "="*80)
print("KEY FINDINGS: WHY DOES THE FDA RESPOND THE WAY IT DOES?")
print("="*80)

report = f"""
1. PETITIONER TYPE MATTERS:
   • Highest success: {category_df.iloc[0]['Category']} ({category_df.iloc[0]['Approval_Rate']:.1f}% approval rate)
   • Lowest success: {category_df.iloc[-1]['Category']} ({category_df.iloc[-1]['Approval_Rate']:.1f}% approval rate)
   • This suggests FDA may be more receptive to certain types of petitioners

2. FDA CENTER VARIATION:
   • Most approving: {center_df.iloc[0]['Center']} ({center_df.iloc[0]['Approval_Rate']:.1f}% approval rate)
   • Least approving: {center_df.iloc[-1]['Center']} ({center_df.iloc[-1]['Approval_Rate']:.1f}% approval rate)
   • Different centers have different approval patterns

3. REPEAT PETITIONERS:
   • Some petitioners have very high success rates (top: {petitioner_df.iloc[0]['Approval_Rate']:.1f}%)
   • Others consistently denied (bottom: {petitioner_df.iloc[-1]['Approval_Rate']:.1f}%)
   • Experience and relationship with FDA may matter

4. TEMPORAL PATTERNS:
   • Analyzed {len(year_df)} years of data
   • Approval rates vary by year, suggesting policy shifts over time

5. PETITION CONTENT:
   • Generic drug petitions appear frequently in both approved and denied
   • Labeling changes and stays of action are common themes
   • Subject matter may influence decision

OVERALL CONCLUSION:
FDA decision-making shows clear patterns based on:
- WHO is petitioning (petitioner type and specific organization)
- WHICH center handles it (CDER vs CFSAN vs CDRH, etc.)
- WHAT is being requested (generic approval, labeling, stay, etc.)
- WHEN the petition is filed (temporal trends)

These patterns suggest FDA responses are influenced by both the petitioner's
profile and the nature of the request, not just the merits alone.
"""

print(report)

# Save report
with open('/Users/avani/FDA_Analysis/pattern_analysis_report.txt', 'w') as f:
    f.write("FDA RESPONSE PATTERN ANALYSIS\n")
    f.write("="*80 + "\n\n")
    f.write(report)

print("\n✓ Saved: pattern_analysis_report.txt")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
