#!/usr/bin/env python3
"""
Visualize FDA Rationale Patterns
Uses enhanced categories from CATEGORY_DEFINITIONS.md
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Load data with enhanced categories
df = pd.read_csv('/Users/avani/FDA_Analysis/fda_rationales_enhanced_categories.csv')

print("Creating visualizations of FDA rationale patterns...")

# Create figure with subplots
fig = plt.figure(figsize=(16, 12))

# ============================================================================
# 1. APPROVAL REASONS
# ============================================================================

ax1 = plt.subplot(2, 2, 1)

approvals = df[df['Decision'] == 'Approved']
approval_counts = approvals['Enhanced_Category'].value_counts()

colors_approval = ['#2ecc71', '#27ae60', '#16a085', '#1abc9c', '#3498db', '#2980b9']
approval_counts.plot(kind='barh', ax=ax1, color=colors_approval[:len(approval_counts)])

ax1.set_title('FDA Approval Reasoning Patterns\n(n=' + str(len(approvals)) + ' approvals)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Number of Approvals', fontsize=11)
ax1.set_ylabel('FDA Reasoning Category', fontsize=11)
ax1.grid(axis='x', alpha=0.3)

# Add counts on bars
for i, v in enumerate(approval_counts):
    ax1.text(v + 2, i, str(v), va='center', fontsize=10, fontweight='bold')

# ============================================================================
# 2. DENIAL REASONS
# ============================================================================

ax2 = plt.subplot(2, 2, 2)

denials = df[df['Decision'] == 'Denied']
denial_counts = denials['Enhanced_Category'].value_counts()

# Color procedural vs substantive based on CATEGORY_DEFINITIONS.md
procedural_categories = [
    'Procedural - Premature/Pending',
    'Procedural - Administrative Deficiency',
    'Procedural - Already Addressed/Moot',
    'Enforcement Discretion'
]

colors_denial = []
for category in denial_counts.index:
    if category in procedural_categories:
        colors_denial.append('#e74c3c')  # Red for procedural
    else:
        colors_denial.append('#f39c12')  # Orange for substantive

denial_counts.plot(kind='barh', ax=ax2, color=colors_denial)

ax2.set_title('FDA Denial Reasoning Patterns\n(n=' + str(len(denials)) + ' denials)', fontsize=14, fontweight='bold')
ax2.set_xlabel('Number of Denials', fontsize=11)
ax2.set_ylabel('FDA Reasoning Category', fontsize=11)
ax2.grid(axis='x', alpha=0.3)

# Add counts on bars
for i, v in enumerate(denial_counts):
    ax2.text(v + 2, i, str(v), va='center', fontsize=10, fontweight='bold')

# Add legend for color coding
procedural_patch = mpatches.Patch(color='#e74c3c', label='Procedural Dismissal')
substantive_patch = mpatches.Patch(color='#f39c12', label='Substantive Decision')
ax2.legend(handles=[procedural_patch, substantive_patch], loc='lower right', fontsize=9)

# ============================================================================
# 3. PROCEDURAL VS SUBSTANTIVE BREAKDOWN
# ============================================================================

ax3 = plt.subplot(2, 2, 3)

# Categorize denials as procedural or substantive based on CATEGORY_DEFINITIONS.md
procedural_denials = denials[denials['Enhanced_Category'].isin(procedural_categories)]
substantive_denials = denials[~denials['Enhanced_Category'].isin(procedural_categories + ['Other Denial Reason'])]
other_denials = denials[denials['Enhanced_Category'] == 'Other Denial Reason']

categories = ['Procedural\nDismissals', 'Substantive\nDecisions', 'Other/\nUnclassified']
counts = [len(procedural_denials), len(substantive_denials), len(other_denials)]
percentages = [c/len(denials)*100 for c in counts]

bars = ax3.bar(categories, counts, color=['#e74c3c', '#f39c12', '#95a5a6'], width=0.6)
ax3.set_title('FDA Denials: Procedural vs Substantive\n(n=' + str(len(denials)) + ' denials)', fontsize=14, fontweight='bold')
ax3.set_ylabel('Number of Denials', fontsize=11)
ax3.grid(axis='y', alpha=0.3)

# Add counts and percentages on bars
for i, (bar, count, pct) in enumerate(zip(bars, counts, percentages)):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2, height + 5,
             f'{count}\n({pct:.1f}%)',
             ha='center', va='bottom', fontsize=12, fontweight='bold')

ax3.set_ylim(0, max(counts) * 1.15)

# ============================================================================
# 4. APPROVAL VS DENIAL OVERVIEW
# ============================================================================

ax4 = plt.subplot(2, 2, 4)

decision_counts = df['Decision'].value_counts()

# Filter to main categories
main_decisions = decision_counts[decision_counts.index.isin(['Approved', 'Denied'])]

colors_overview = {'Approved': '#2ecc71', 'Denied': '#e74c3c'}
colors = [colors_overview.get(x, '#95a5a6') for x in main_decisions.index]

explode = (0.05, 0.05)
wedges, texts, autotexts = ax4.pie(main_decisions, labels=main_decisions.index,
                                      autopct='%1.1f%%', startangle=90,
                                      colors=colors, explode=explode,
                                      textprops={'fontsize': 12, 'fontweight': 'bold'})

ax4.set_title('Overall FDA Decisions\n(n=' + str(main_decisions.sum()) + ' with decision)', fontsize=14, fontweight='bold')

# Add counts
for i, (wedge, count) in enumerate(zip(wedges, main_decisions)):
    angle = (wedge.theta2 - wedge.theta1) / 2. + wedge.theta1
    import numpy as np
    x = wedge.r * 0.7 * np.cos(np.deg2rad(angle))
    y = wedge.r * 0.7 * np.sin(np.deg2rad(angle))
    ax4.text(x, y, f'n={count}', ha='center', va='center',
             fontsize=11, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# ============================================================================
# OVERALL TITLE AND LAYOUT
# ============================================================================

fig.suptitle('FDA Citizen Petition Response Rationale Analysis\n' +
             'How the FDA Justifies Approvals and Denials (2000-2024)',
             fontsize=16, fontweight='bold', y=0.995)

plt.tight_layout(rect=[0, 0, 1, 0.98])

# Save
output_path = '/Users/avani/FDA_Analysis/viz_fda_rationales.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✓ Saved: {output_path}")

# ============================================================================
# SECOND FIGURE: DETAILED CATEGORY COMPARISON
# ============================================================================

fig2, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(14, 10))

# Top: All approval categories
approval_counts_all = approvals['Enhanced_Category'].value_counts()

approval_counts_all.plot(kind='bar', ax=ax_top, color='#2ecc71', width=0.7)
ax_top.set_title('FDA Approval Reasoning - Detailed Breakdown (n=' + str(len(approvals)) + ')',
                 fontsize=13, fontweight='bold')
ax_top.set_ylabel('Number of Approvals', fontsize=11)
ax_top.set_xlabel('')
ax_top.grid(axis='y', alpha=0.3)
ax_top.tick_params(axis='x', rotation=45)

for i, v in enumerate(approval_counts_all):
    ax_top.text(i, v + 1, str(v), ha='center', va='bottom',
                fontsize=10, fontweight='bold')

# Bottom: All denial categories with color coding
denial_counts_all = denials['Enhanced_Category'].value_counts()

colors_detailed = []
for category in denial_counts_all.index:
    if category in procedural_categories:
        colors_detailed.append('#e74c3c')
    else:
        colors_detailed.append('#f39c12')

denial_counts_all.plot(kind='bar', ax=ax_bottom, color=colors_detailed, width=0.7)
ax_bottom.set_title('FDA Denial Reasoning - Detailed Breakdown (n=' + str(len(denials)) + ')\n' +
                    'Red = Procedural Dismissal | Orange = Substantive Decision',
                    fontsize=13, fontweight='bold')
ax_bottom.set_ylabel('Number of Denials', fontsize=11)
ax_bottom.set_xlabel('FDA Reasoning Category', fontsize=11)
ax_bottom.grid(axis='y', alpha=0.3)
ax_bottom.tick_params(axis='x', rotation=45)

for i, v in enumerate(denial_counts_all):
    ax_bottom.text(i, v + 1, str(v), ha='center', va='bottom',
                   fontsize=10, fontweight='bold')

plt.tight_layout()

output_path2 = '/Users/avani/FDA_Analysis/viz_fda_rationales_detailed.png'
plt.savefig(output_path2, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✓ Saved: {output_path2}")

print("\n" + "="*80)
print("VISUALIZATIONS COMPLETE")
print("="*80)
print(f"Created 2 visualizations:")
print(f"  1. {output_path}")
print(f"  2. {output_path2}")
