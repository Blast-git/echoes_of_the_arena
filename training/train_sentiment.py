"""
=============================================================================
  Echoes of the Arena — Sentiment Classifier Training Script
  File: training/train_sentiment.py
=============================================================================

  Supervised Learning: TF-IDF + Logistic Regression Pipeline
  Task: Classify RPG rumors as Honorable (1) or Dishonorable (0)

=============================================================================
"""

import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    accuracy_score,
)

# ── Output directories ────────────────────────────────────────────────────────
os.makedirs("data",   exist_ok=True)
os.makedirs("models", exist_ok=True)


# =============================================================================
#  Mock Dataset  (60+ RPG rumors)
# =============================================================================

RUMORS = [
    # ── Positive / Honorable  (label = 1) ────────────────────────────────────
    ("He fought with true valor and never struck a fallen foe.",                    1),
    ("A fair and noble knight, respected by all in the arena.",                     1),
    ("She bowed to her opponent before the duel even began.",                       1),
    ("He offered water to his wounded rival after the match.",                      1),
    ("The champion refused to finish a defenseless opponent.",                      1),
    ("She trained every dawn to earn her victories honestly.",                      1),
    ("He returned stolen gold to the merchant without hesitation.",                 1),
    ("The gladiator shielded a child from a rogue arrow mid-battle.",               1),
    ("She carried her fallen enemy off the field with dignity.",                    1),
    ("He challenged only those who could truly fight back.",                        1),
    ("The warrior dropped his weapon when his foe was disarmed.",                   1),
    ("She never used magic in a contest of pure steel.",                            1),
    ("He confessed to his lord when he made a grave error in judgment.",            1),
    ("The knight gave his rations to starving villagers on the march.",             1),
    ("She stood alone against three bandits to protect a traveler.",                1),
    ("He threw down his shield so the duel would be equal.",                        1),
    ("She refused a bribe to throw the championship bout.",                         1),
    ("He warned his enemy of the trap before the fight began.",                     1),
    ("The paladin healed both friend and foe after the siege.",                     1),
    ("She fought a fair rematch after her opponent slipped on wet stone.",          1),
    ("He accepted defeat graciously and praised his victor openly.",                1),
    ("She donated her entire prize purse to the widows of fallen soldiers.",        1),
    ("The swordsman practiced mercy even when the crowd demanded blood.",           1),
    ("He refused to ambush the enemy camp while they slept.",                       1),
    ("She is known across seven cities for keeping every oath she makes.",          1),
    ("He stepped between his comrade and a cowardly backstab without thought.",     1),
    ("The duelist never once struck an unarmed man, even in anger.",                1),
    ("She returned the enemy banner with honor after the siege was won.",           1),
    ("He carries every scar with pride, each earned in a fair contest.",            1),
    ("She challenged the corrupt magistrate to open trial by combat.",              1),

    # ── Negative / Dishonorable  (label = 0) ─────────────────────────────────
    ("He threw sand in my eyes like a coward before striking.",                     0),
    ("He used dark poison on his blade before the tournament.",                     0),
    ("She bribed the referee to overlook her illegal elbow strikes.",               0),
    ("He stabbed his opponent in the back during the ceremonial bow.",              0),
    ("The mercenary slaughtered the surrendering garrison for sport.",              0),
    ("She slipped venom into the champion's drinking water before the bout.",       0),
    ("He lied under sacred oath to avoid punishment for his crimes.",               0),
    ("The rogue cut the saddle strap on his rival's horse before the joust.",       0),
    ("She hired assassins to eliminate the competition before the finals.",         0),
    ("He fled the battlefield and left his allies to die for a distraction.",       0),
    ("The villain used forbidden shadow magic to blind the referee.",               0),
    ("She spread false rumors to destroy a rival's reputation without proof.",      0),
    ("He attacked an unarmed healer during the truce of the harvest moon.",         0),
    ("The schemer poisoned the well to weaken the entire opposing camp.",           0),
    ("She paid street thugs to break the champion's sword hand before dawn.",       0),
    ("He sold his comrades' positions to the enemy for a pouch of coin.",           0),
    ("The thug ambushed travelers on the road to loot the prize caravan.",          0),
    ("She used an illegal concealed dagger strapped beneath her gauntlet.",         0),
    ("He lured his enemy into a pit trap disguised as a shortcut.",                 0),
    ("The warlock sacrificed prisoners to gain cursed power for the duel.",         0),
    ("She feigned surrender then drove a hidden spike through the guard.",          0),
    ("He bribed the arena master to pair him only with injured opponents.",         0),
    ("The sneak struck from the shadows during a sworn ceasefire.",                 0),
    ("She used alchemical fumes to disorient her opponent in an enclosed ring.",    0),
    ("He ordered his men to burn the village as a bargaining chip.",                0),
    ("The coward tripped his rival on the steps before the championship match.",    0),
    ("She colluded with the bookmaker to fix every bout in the season.",            0),
    ("He stole his rival's enchanted armor the night before the grand melee.",      0),
    ("The mercenary executed wounded prisoners in violation of the code.",          0),
    ("She poisoned the forge master to ensure her weapons would be superior.",      0),
]

# Validation
assert len(RUMORS) >= 60, f"Need at least 60 rumors, got {len(RUMORS)}"

df = pd.DataFrame(RUMORS, columns=["text", "label"])
csv_path = os.path.join("data", "mock_rumors.csv")
df.to_csv(csv_path, index=False)
print(f"\n  Dataset saved → {csv_path}  ({len(df)} rumors)\n")


# =============================================================================
#  Train / Test Split
# =============================================================================

X = df["text"]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

print(f"  Train samples : {len(X_train)}")
print(f"  Test  samples : {len(X_test)}")
print(f"  Class balance (train) — Honorable: {sum(y_train==1)}  "
      f"Dishonorable: {sum(y_train==0)}\n")


# =============================================================================
#  ML Pipeline  (TF-IDF  +  Logistic Regression)
# =============================================================================

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),     # unigrams + bigrams
        min_df=1,
        max_features=5_000,
        sublinear_tf=True,      # log-scale TF scaling
    )),
    ("clf", LogisticRegression(
        C=1.0,
        max_iter=1_000,
        solver="lbfgs",
        random_state=42,
    )),
])

pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)


# =============================================================================
#  Terminal Report  (screenshot-ready)
# =============================================================================

BORDER = "═" * 62
THIN = "─" * 62

print(f"\n  {BORDER}")
print(f"  {'ECHOES OF THE ARENA — SENTIMENT CLASSIFIER REPORT':^60}")
print(f"  {BORDER}")
print(f"\n  Accuracy : {accuracy_score(y_test, y_pred)*100:.1f}%\n")
print(f"  {THIN}")
print(f"  {'CLASSIFICATION REPORT':^60}")
print(f"  {THIN}")
report = classification_report(
    y_test, y_pred,
    target_names=["Dishonorable (0)", "Honorable (1)"],
    digits=3,
)
for line in report.splitlines():
    print(f"  {line}")

cm = confusion_matrix(y_test, y_pred)
print(f"\n  {THIN}")
print(f"  {'CONFUSION MATRIX':^60}")
print(f"  {THIN}")
print(f"  {'':20} Predicted Dis.  Predicted Hon.")
print(f"  {'Actual Dishonorable':<22}   {cm[0,0]:^13}  {cm[0,1]:^14}")
print(f"  {'Actual Honorable':<22}   {cm[1,0]:^13}  {cm[1,1]:^14}")
print(f"  {BORDER}\n")


# =============================================================================
#  Confusion Matrix Plot
# =============================================================================

fig, ax = plt.subplots(figsize=(6, 5))
fig.patch.set_facecolor("#1a1a2e")
ax.set_facecolor("#16213e")

disp = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=["Dishonorable", "Honorable"],
)
disp.plot(ax=ax, colorbar=False, cmap="RdPu")

ax.set_title("Confusion Matrix — RPG Rumor Classifier",
             color="white", fontsize=12, fontweight="bold", pad=12)
ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white")
ax.tick_params(colors="white")
for text in disp.text_.ravel():
    text.set_color("white")
    text.set_fontsize(14)
    text.set_fontweight("bold")
for spine in ax.spines.values():
    spine.set_edgecolor("#444466")

plt.tight_layout()
cm_path = os.path.join("models", "confusion_matrix.png")
plt.savefig(cm_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"  Confusion matrix plot saved → {cm_path}")


# =============================================================================
#  Feature Importance Plot  (top TF-IDF tokens per class)
# =============================================================================

tfidf = pipeline.named_steps["tfidf"]
clf = pipeline.named_steps["clf"]
tokens = np.array(tfidf.get_feature_names_out())
coefs = clf.coef_[0]

TOP_N = 15
top_hon_idx = np.argsort(coefs)[-TOP_N:][::-1]
top_dis_idx = np.argsort(coefs)[:TOP_N]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.patch.set_facecolor("#1a1a2e")
fig.suptitle("Top Predictive Tokens — Logistic Regression Coefficients",
             color="white", fontsize=13, fontweight="bold", y=1.02)

for ax, idx, color, title in [
    (axes[0], top_hon_idx, "#4ade80", "Honorable Tokens (+)"),
    (axes[1], top_dis_idx, "#f87171", "Dishonorable Tokens (−)"),
]:
    ax.set_facecolor("#16213e")
    vals = coefs[idx]
    labels = tokens[idx]
    bars = ax.barh(range(TOP_N), vals, color=color, alpha=0.85)
    ax.set_yticks(range(TOP_N))
    ax.set_yticklabels(labels, color="white", fontsize=9)
    ax.set_xlabel("Coefficient weight", color="#aaaaaa")
    ax.set_title(title, color="white", fontsize=11, fontweight="bold")
    ax.tick_params(axis="x", colors="#aaaaaa")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444466")
    ax.invert_yaxis()

plt.tight_layout()
feat_path = os.path.join("models", "feature_importance.png")
plt.savefig(feat_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"  Feature importance plot saved → {feat_path}")


# =============================================================================
#  Save Pipeline Components
# =============================================================================

model_path = os.path.join("models", "sentiment_model.pkl")
vec_path = os.path.join("models", "tfidf_vectorizer.pkl")

joblib.dump(pipeline.named_steps["clf"],   model_path)
joblib.dump(pipeline.named_steps["tfidf"], vec_path)

print(f"  Model saved      → {model_path}")
print(f"  Vectorizer saved → {vec_path}")


# =============================================================================
#  Quick Inference Demo
# =============================================================================

TEST_RUMORS = [
    "He fought with great honor and spared the defeated warrior.",
    "She used poison and bribed the judges to win the title.",
    "A mysterious stranger appeared at the gates of the coliseum.",
]

print(f"\n  {'─'*62}")
print(f"  {'INFERENCE DEMO':^60}")
print(f"  {'─'*62}")
for rumor in TEST_RUMORS:
    pred = pipeline.predict([rumor])[0]
    proba = pipeline.predict_proba([rumor])[0]
    label = "✅ Honorable" if pred == 1 else "☠️  Dishonorable"
    conf = max(proba) * 100
    print(f"  [{label}] ({conf:.1f}% conf)")
    print(f"   \"{rumor}\"\n")
