import joblib
import os

# 1. Safely locate the models folder
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
vec_path = os.path.join(project_root, "models", "tfidf_vectorizer.pkl")
mod_path = os.path.join(project_root, "models", "sentiment_model.pkl")

print("🔍 Loading NLP Pipeline...")
try:
    vectorizer = joblib.load(vec_path)
    model = joblib.load(mod_path)
    print("✅ Vectorizer and Model loaded successfully!\n")
except FileNotFoundError:
    print("❌ Error: Could not find the .pkl files. Make sure they are in the models/ folder.")
    exit()

# 2. Create some fake LLM-generated rumors to test
test_rumors = [
    "He fought bravely and bowed before striking.",  # Should be 1 (Honorable)
    "He is a coward who threw sand and used poison.", # Should be 0 (Dishonorable)
    "A clean and fair victory for the gladiator.",    # Should be 1 (Honorable)
    "He stabbed him in the back. A dirty trickster!"  # Should be 0 (Dishonorable)
]

# 3. Transform the text into math using the Vectorizer
print("=== RUNNING INFERENCE TESTS ===\n")
X_test_vec = vectorizer.transform(test_rumors)

# 4. Predict the sentiment
predictions = model.predict(X_test_vec)
probabilities = model.predict_proba(X_test_vec) # Gets the confidence %

# 5. Display the results
for i in range(len(test_rumors)):
    rumor = test_rumors[i]
    pred = predictions[i]
    confidence = probabilities[i][pred] * 100
    
    label = "🟩 HONORABLE (1)" if pred == 1 else "🟥 DISHONORABLE (0)"
    
    print(f"Rumor: '{rumor}'")
    print(f"Prediction: {label} (Confidence: {confidence:.2f}%)\n")