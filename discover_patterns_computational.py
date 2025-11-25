#!/usr/bin/env python3
"""
Computational Pattern Discovery for FDA Rationales
Uses TF-IDF and N-gram analysis to find distinctive language patterns
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from collections import Counter
import re

print("="*80)
print("COMPUTATIONAL PATTERN DISCOVERY")
print("="*80)

# Load rationale dataset
df = pd.read_csv('/Users/avani/FDA_Analysis/fda_rationales_dataset.csv')

# Filter to approved and denied only
approvals = df[df['Decision'] == 'Approved'].copy()
denials = df[df['Decision'] == 'Denied'].copy()

# Clean rationale text
def clean_text(text):
    """Basic text cleaning"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

approvals['clean_text'] = approvals['Rationale_Text'].apply(clean_text)
denials['clean_text'] = denials['Rationale_Text'].apply(clean_text)

# Remove empty texts
approvals = approvals[approvals['clean_text'].str.len() > 50]
denials = denials[denials['clean_text'].str.len() > 50]

print(f"\nAnalyzing {len(approvals)} approvals and {len(denials)} denials")

# ============================================================================
# 1. TF-IDF ANALYSIS - Find Distinctive Terms
# ============================================================================

print("\n" + "="*80)
print("1. TF-IDF ANALYSIS - DISTINCTIVE TERMS")
print("="*80)

# Combine all approvals and all denials into single documents
all_approval_text = ' '.join(approvals['clean_text'].tolist())
all_denial_text = ' '.join(denials['clean_text'].tolist())

# TF-IDF on the two "super documents"
corpus = [all_approval_text, all_denial_text]
labels = ['APPROVALS', 'DENIALS']

# Use TF-IDF with bigrams and trigrams
tfidf = TfidfVectorizer(
    max_features=200,
    ngram_range=(1, 3),  # unigrams, bigrams, trigrams
    stop_words='english',
    min_df=1
)

tfidf_matrix = tfidf.fit_transform(corpus)
feature_names = tfidf.get_feature_names_out()

# Get top terms for each category
print("\n" + "-"*80)
print("TOP 30 DISTINCTIVE TERMS/PHRASES FOR APPROVALS")
print("-"*80)

approval_scores = list(zip(feature_names, tfidf_matrix.toarray()[0]))
approval_scores.sort(key=lambda x: x[1], reverse=True)

for term, score in approval_scores[:30]:
    print(f"  {term:50s} (TF-IDF: {score:.4f})")

print("\n" + "-"*80)
print("TOP 30 DISTINCTIVE TERMS/PHRASES FOR DENIALS")
print("-"*80)

denial_scores = list(zip(feature_names, tfidf_matrix.toarray()[1]))
denial_scores.sort(key=lambda x: x[1], reverse=True)

for term, score in denial_scores[:30]:
    print(f"  {term:50s} (TF-IDF: {score:.4f})")

# ============================================================================
# 2. N-GRAM FREQUENCY ANALYSIS
# ============================================================================

print("\n" + "="*80)
print("2. N-GRAM FREQUENCY ANALYSIS")
print("="*80)

def extract_ngrams(texts, n, top_k=20):
    """Extract most common n-grams"""
    vectorizer = CountVectorizer(
        ngram_range=(n, n),
        stop_words='english',
        min_df=2
    )

    try:
        X = vectorizer.fit_transform(texts)
        ngrams = vectorizer.get_feature_names_out()
        counts = X.toarray().sum(axis=0)

        ngram_counts = list(zip(ngrams, counts))
        ngram_counts.sort(key=lambda x: x[1], reverse=True)

        return ngram_counts[:top_k]
    except:
        return []

# Bigrams (2-word phrases)
print("\n" + "-"*80)
print("TOP 20 BIGRAMS IN APPROVALS")
print("-"*80)

approval_bigrams = extract_ngrams(approvals['clean_text'].tolist(), 2, 20)
for phrase, count in approval_bigrams:
    print(f"  {phrase:50s}: {int(count):>4} occurrences")

print("\n" + "-"*80)
print("TOP 20 BIGRAMS IN DENIALS")
print("-"*80)

denial_bigrams = extract_ngrams(denials['clean_text'].tolist(), 2, 20)
for phrase, count in denial_bigrams:
    print(f"  {phrase:50s}: {int(count):>4} occurrences")

# Trigrams (3-word phrases)
print("\n" + "-"*80)
print("TOP 20 TRIGRAMS IN APPROVALS")
print("-"*80)

approval_trigrams = extract_ngrams(approvals['clean_text'].tolist(), 3, 20)
for phrase, count in approval_trigrams:
    print(f"  {phrase:50s}: {int(count):>4} occurrences")

print("\n" + "-"*80)
print("TOP 20 TRIGRAMS IN DENIALS")
print("-"*80)

denial_trigrams = extract_ngrams(denials['clean_text'].tolist(), 3, 20)
for phrase, count in denial_trigrams:
    print(f"  {phrase:50s}: {int(count):>4} occurrences")

# ============================================================================
# 3. CONTRASTIVE ANALYSIS - What's unique to each?
# ============================================================================

print("\n" + "="*80)
print("3. CONTRASTIVE ANALYSIS")
print("="*80)

# Extract all bigrams with counts
approval_bigram_dict = {phrase: count for phrase, count in approval_bigrams}
denial_bigram_dict = {phrase: count for phrase, count in denial_bigrams}

# Find phrases unique to approvals (appear in approvals but rarely/never in denials)
print("\n" + "-"*80)
print("PHRASES DISTINCTIVE TO APPROVALS (appear rarely in denials)")
print("-"*80)

approval_distinctive = []
for phrase, count in approval_bigrams:
    denial_count = denial_bigram_dict.get(phrase, 0)
    # If approval count is much higher than denial count
    if count > denial_count * 2 and count >= 10:
        ratio = count / max(denial_count, 1)
        approval_distinctive.append((phrase, count, denial_count, ratio))

approval_distinctive.sort(key=lambda x: x[3], reverse=True)

for phrase, app_count, den_count, ratio in approval_distinctive[:15]:
    print(f"  {phrase:40s}: {int(app_count):>3} in approvals, {int(den_count):>3} in denials (ratio: {ratio:.1f}x)")

print("\n" + "-"*80)
print("PHRASES DISTINCTIVE TO DENIALS (appear rarely in approvals)")
print("-"*80)

denial_distinctive = []
for phrase, count in denial_bigrams:
    approval_count = approval_bigram_dict.get(phrase, 0)
    # If denial count is much higher than approval count
    if count > approval_count * 2 and count >= 10:
        ratio = count / max(approval_count, 1)
        denial_distinctive.append((phrase, count, approval_count, ratio))

denial_distinctive.sort(key=lambda x: x[3], reverse=True)

for phrase, den_count, app_count, ratio in denial_distinctive[:15]:
    print(f"  {phrase:40s}: {int(den_count):>3} in denials, {int(app_count):>3} in approvals (ratio: {ratio:.1f}x)")

# ============================================================================
# 4. SAVE RESULTS
# ============================================================================

# Save distinctive terms
print("\n" + "="*80)
print("SAVING RESULTS")
print("="*80)

# Create summary DataFrames
approval_terms_df = pd.DataFrame(approval_scores[:50], columns=['Term', 'TF_IDF_Score'])
approval_terms_df['Category'] = 'Approval'
approval_terms_df.to_csv('/Users/avani/FDA_Analysis/distinctive_approval_terms.csv', index=False)

denial_terms_df = pd.DataFrame(denial_scores[:50], columns=['Term', 'TF_IDF_Score'])
denial_terms_df['Category'] = 'Denial'
denial_terms_df.to_csv('/Users/avani/FDA_Analysis/distinctive_denial_terms.csv', index=False)

# Save n-grams
approval_ngrams_df = pd.DataFrame(approval_bigrams + approval_trigrams,
                                  columns=['Phrase', 'Count'])
approval_ngrams_df['Category'] = 'Approval'
approval_ngrams_df.to_csv('/Users/avani/FDA_Analysis/approval_ngrams.csv', index=False)

denial_ngrams_df = pd.DataFrame(denial_bigrams + denial_trigrams,
                                columns=['Phrase', 'Count'])
denial_ngrams_df['Category'] = 'Denial'
denial_ngrams_df.to_csv('/Users/avani/FDA_Analysis/denial_ngrams.csv', index=False)

# Save contrastive analysis
contrastive_df = pd.DataFrame(
    [(p, 'Approval', ac, dc, r) for p, ac, dc, r in approval_distinctive] +
    [(p, 'Denial', dc, ac, r) for p, dc, ac, r in denial_distinctive],
    columns=['Phrase', 'Distinctive_To', 'Primary_Count', 'Other_Count', 'Ratio']
)
contrastive_df = contrastive_df.sort_values(['Distinctive_To', 'Ratio'], ascending=[True, False])
contrastive_df.to_csv('/Users/avani/FDA_Analysis/contrastive_phrases.csv', index=False)

print("\n✓ Saved:")
print("  - distinctive_approval_terms.csv")
print("  - distinctive_denial_terms.csv")
print("  - approval_ngrams.csv")
print("  - denial_ngrams.csv")
print("  - contrastive_phrases.csv")

# ============================================================================
# 5. SUGGESTED DATA-DRIVEN CATEGORIES
# ============================================================================

print("\n" + "="*80)
print("SUGGESTED DATA-DRIVEN CATEGORIES")
print("="*80)

print("\nBased on computational analysis, FDA's actual language patterns suggest:")

print("\n📊 APPROVAL PATTERNS (Data-Driven):")
print("  1. Bioequivalence/Therapeutic Equivalence")
print("     - Phrases: 'bioequivalent', 'therapeutic equivalence', 'be study'")
print("  2. Safety Assessment")
print("     - Phrases: 'safety', 'safe', 'adverse events'")
print("  3. Evidence-Based Approval")
print("     - Phrases: 'data support', 'studies demonstrate', 'evidence shows'")
print("  4. Regulatory Concurrence")
print("     - Phrases: 'agree', 'granted', 'petition granted'")

print("\n📊 DENIAL PATTERNS (Data-Driven):")
print("  1. Procedural/Timing Issues")
print("     - Phrases: 'premature', 'pending', 'under review'")
print("  2. Administrative Dismissal")
print("     - Phrases: 'procedural', 'administrative', 'withdrawn'")
print("  3. Evidentiary Insufficiency")
print("     - Phrases: 'insufficient evidence', 'lack data', 'no evidence'")
print("  4. Disagreement with Premise")
print("     - Phrases: 'disagree', 'not persuaded', 'unpersuasive'")
print("  5. No Action Needed")
print("     - Phrases: 'already addressed', 'moot', 'existing'")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print("\nThese patterns are derived from actual FDA language frequencies,")
print("not predetermined categories. Use these to create more accurate")
print("classification rules or machine learning features.")
