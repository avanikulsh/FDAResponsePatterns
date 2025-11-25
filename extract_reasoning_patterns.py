#!/usr/bin/env python3
"""
Extract FDA Reasoning Patterns
Focus on WHY FDA makes decisions - extract justification clauses
"""

import pandas as pd
import re
from collections import Counter

print("="*80)
print("EXTRACTING FDA REASONING PATTERNS")
print("="*80)

# Load rationale dataset
df = pd.read_csv('/Users/avani/FDA_Analysis/fda_rationales_dataset.csv')

approvals = df[df['Decision'] == 'Approved'].copy()
denials = df[df['Decision'] == 'Denied'].copy()

print(f"\nAnalyzing {len(approvals)} approvals and {len(denials)} denials")

# ============================================================================
# EXTRACT REASONING CLAUSES
# ============================================================================

def extract_reasoning_clauses(text):
    """
    Extract the actual reasoning - text that follows justification markers
    like "because", "based on", "determined that", etc.
    """
    if pd.isna(text):
        return []

    text = str(text).lower()

    # Reasoning markers - phrases that introduce justification
    reasoning_patterns = [
        (r'(?:we (?:are |have )?(?:grant|deny|approv)[a-z]+ (?:the )?(?:petition|request)?)(?:\s+)([^.]{20,150})', 'decision_clause'),
        (r'(?:for the following reasons?:|the reasons? (?:for|are):?)([^.]{20,200})', 'reason_statement'),
        (r'(?:because|as)([^.]{20,150})', 'because_clause'),
        (r'(?:based on|given|considering)([^.]{20,150})', 'based_on_clause'),
        (r'(?:we (?:have )?determined that|the agency (?:has )?(?:determined|concluded) that)([^.]{20,150})', 'determination_clause'),
        (r'(?:after (?:careful )?(?:review|consideration)|upon review)([^.]{20,150})', 'review_clause'),
        (r'(?:there is|we find|we conclude|we note)([^.]{20,150})', 'finding_clause'),
    ]

    clauses = []
    for pattern, clause_type in reasoning_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            clause = match.group(1).strip()
            # Clean up
            clause = re.sub(r'\s+', ' ', clause)
            if len(clause) > 15:  # Minimum length
                clauses.append((clause_type, clause))

    return clauses

print("\n" + "="*80)
print("EXTRACTING REASONING CLAUSES FROM DOCUMENTS")
print("="*80)

# Extract reasoning clauses
approval_clauses = []
for idx, row in approvals.iterrows():
    clauses = extract_reasoning_clauses(row['Rationale_Text'])
    approval_clauses.extend(clauses)

denial_clauses = []
for idx, row in denials.iterrows():
    clauses = extract_reasoning_clauses(row['Rationale_Text'])
    denial_clauses.extend(clauses)

print(f"\nExtracted {len(approval_clauses)} reasoning clauses from approvals")
print(f"Extracted {len(denial_clauses)} reasoning clauses from denials")

# ============================================================================
# IDENTIFY KEY REASONING PATTERNS
# ============================================================================

def identify_reasoning_pattern(clause_text):
    """
    Categorize what type of reasoning this represents
    """
    text = clause_text.lower()

    # APPROVAL REASONING PATTERNS
    if any(word in text for word in ['bioequivalent', 'bioequivalence', 'be study', 'therapeutic equivalence']):
        return 'Bioequivalence Demonstrated'

    elif any(phrase in text for phrase in ['safety', 'safe', 'no safety concern', 'safety profile']):
        return 'Safety Established'

    elif any(phrase in text for phrase in ['public health', 'public interest', 'benefit']):
        return 'Public Health Benefit'

    elif any(phrase in text for phrase in ['data support', 'evidence', 'studies', 'demonstrated']):
        return 'Sufficient Evidence'

    elif any(phrase in text for phrase in ['agree', 'merit', 'warrant', 'appropriate']):
        return 'FDA Agrees/Warrants Action'

    # DENIAL REASONING PATTERNS
    elif any(phrase in text for phrase in ['premature', 'pending', 'ongoing', 'under review', 'not yet']):
        return 'Premature/Pending Action'

    elif any(phrase in text for phrase in ['insufficient', 'lack', 'inadequate', 'no evidence', 'no data']):
        return 'Insufficient Evidence'

    elif any(phrase in text for phrase in ['disagree', 'not persuaded', 'unpersuasive', 'not support']):
        return 'FDA Disagrees'

    elif any(phrase in text for phrase in ['moot', 'already', 'existing', 'previously addressed']):
        return 'Already Addressed/Moot'

    elif any(phrase in text for phrase in ['no authority', 'outside scope', 'jurisdiction', 'not appropriate']):
        return 'Outside FDA Authority'

    elif any(phrase in text for phrase in ['procedural', 'administrative', 'regulation', '21 cfr 10']):
        return 'Procedural Issue'

    elif any(phrase in text for phrase in ['enforcement discretion', 'priorities', 'resources']):
        return 'Enforcement Discretion'

    elif any(phrase in text for phrase in ['no public health', 'no safety concern', 'no risk']):
        return 'No Public Health Concern'

    else:
        return 'Other/Unspecified'

# Categorize all clauses
print("\n" + "="*80)
print("CATEGORIZING REASONING PATTERNS")
print("="*80)

approval_patterns = []
for clause_type, clause_text in approval_clauses:
    pattern = identify_reasoning_pattern(clause_text)
    approval_patterns.append((pattern, clause_text))

denial_patterns = []
for clause_type, clause_text in denial_clauses:
    pattern = identify_reasoning_pattern(clause_text)
    denial_patterns.append((pattern, clause_text))

# Count patterns
approval_pattern_counts = Counter([p for p, _ in approval_patterns])
denial_pattern_counts = Counter([p for p, _ in denial_patterns])

print("\n" + "-"*80)
print("APPROVAL REASONING PATTERNS")
print("-"*80)
for pattern, count in approval_pattern_counts.most_common():
    print(f"  {pattern:40s}: {count:>4} occurrences")

print("\n" + "-"*80)
print("DENIAL REASONING PATTERNS")
print("-"*80)
for pattern, count in denial_pattern_counts.most_common():
    print(f"  {pattern:40s}: {count:>4} occurrences")

# ============================================================================
# SHOW EXAMPLE REASONING CLAUSES
# ============================================================================

print("\n" + "="*80)
print("EXAMPLE REASONING CLAUSES")
print("="*80)

def show_examples(patterns, category, n=5):
    """Show n example clauses for a category"""
    examples = [text for pattern, text in patterns if pattern == category]
    if examples:
        print(f"\n{category}:")
        print("-" * 80)
        for i, example in enumerate(examples[:n], 1):
            # Truncate long examples
            display_text = example[:200] + "..." if len(example) > 200 else example
            print(f"  {i}. {display_text}")

# Show examples for top approval patterns
print("\n" + "="*80)
print("APPROVAL REASONING EXAMPLES")
print("="*80)

for pattern, count in approval_pattern_counts.most_common(5):
    show_examples(approval_patterns, pattern, 3)

# Show examples for top denial patterns
print("\n" + "="*80)
print("DENIAL REASONING EXAMPLES")
print("="*80)

for pattern, count in denial_pattern_counts.most_common(5):
    show_examples(denial_patterns, pattern, 3)

# ============================================================================
# SAVE RESULTS
# ============================================================================

print("\n" + "="*80)
print("SAVING RESULTS")
print("="*80)

# Save all reasoning clauses with categories
approval_reasoning_df = pd.DataFrame(approval_patterns, columns=['Pattern', 'Reasoning_Clause'])
approval_reasoning_df['Decision'] = 'Approval'
approval_reasoning_df.to_csv('/Users/avani/FDA_Analysis/approval_reasoning_clauses.csv', index=False)

denial_reasoning_df = pd.DataFrame(denial_patterns, columns=['Pattern', 'Reasoning_Clause'])
denial_reasoning_df['Decision'] = 'Denial'
denial_reasoning_df.to_csv('/Users/avani/FDA_Analysis/denial_reasoning_clauses.csv', index=False)

# Save pattern summaries
approval_summary = pd.DataFrame(approval_pattern_counts.most_common(),
                               columns=['Pattern', 'Count'])
approval_summary['Decision'] = 'Approval'

denial_summary = pd.DataFrame(denial_pattern_counts.most_common(),
                             columns=['Pattern', 'Count'])
denial_summary['Decision'] = 'Denial'

combined_summary = pd.concat([approval_summary, denial_summary], ignore_index=True)
combined_summary.to_csv('/Users/avani/FDA_Analysis/reasoning_pattern_summary.csv', index=False)

print("\n✓ Saved:")
print("  - approval_reasoning_clauses.csv (all extracted reasoning clauses)")
print("  - denial_reasoning_clauses.csv (all extracted reasoning clauses)")
print("  - reasoning_pattern_summary.csv (pattern counts)")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

total_approval_clauses = len(approval_patterns)
total_denial_clauses = len(denial_patterns)

print(f"\nTotal reasoning clauses extracted:")
print(f"  Approvals: {total_approval_clauses}")
print(f"  Denials: {total_denial_clauses}")

print(f"\nDistinct reasoning patterns:")
print(f"  Approvals: {len(approval_pattern_counts)}")
print(f"  Denials: {len(denial_pattern_counts)}")

print(f"\nMost common approval reasoning:")
if approval_pattern_counts:
    top_approval = approval_pattern_counts.most_common(1)[0]
    print(f"  {top_approval[0]}: {top_approval[1]} ({top_approval[1]/total_approval_clauses*100:.1f}%)")

print(f"\nMost common denial reasoning:")
if denial_pattern_counts:
    top_denial = denial_pattern_counts.most_common(1)[0]
    print(f"  {top_denial[0]}: {top_denial[1]} ({top_denial[1]/total_denial_clauses*100:.1f}%)")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
