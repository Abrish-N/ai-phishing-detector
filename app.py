from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pickle
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
CORS(app)

# =========================
# 🔹 LOAD TRAINED MODEL
# =========================
with (BASE_DIR / "model.pkl").open("rb") as model_file:
    model = pickle.load(model_file)
with (BASE_DIR / "vectorizer.pkl").open("rb") as vectorizer_file:
    vectorizer = pickle.load(vectorizer_file)


@app.route("/")
def index():
    return render_template("index.html")


def clean_text(text):
    text = (text or "").lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# =========================
# 🔹 HELPER FUNCTIONS
# =========================
brands = ["paypal", "google", "faysalbank", "facebook"]
trusted_domains = [
    "nu.edu.pk",
    "jsbank.lmtd.com",
    "classroom.google.com",
]

def detect_typosquatting(domain):
    suspicious = []
    for brand in brands:
        if brand in domain and domain != brand + ".com":
            suspicious.append(f"Possible fake domain: {domain}")
    return suspicious

def get_sender_domain(sender):
    if not sender:
        return None
    sender = sender.lower().strip()
    match = re.search(r"[\w.-]+@([\w.-]+)", sender)
    if match:
        return match.group(1)
    if "." in sender:
        return sender
    return None


def is_trusted_sender(sender):
    domain = get_sender_domain(sender)
    return domain in trusted_domains if domain else False


# =========================
# 🔹 MAIN API
# =========================
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON request body is required"}), 400

    subject = str(data.get("subject", "")).strip()
    body = str(data.get("body", data.get("text", ""))).strip()
    text = f"{subject} {body}".strip()
    sender = data.get("sender")

    if not text:
        return jsonify({"error": "subject or body text is required"}), 400

    display_text = text.lower()

    reasons = set()   # prevents duplicates

    if is_trusted_sender(sender):
        reasons.add(f"Trusted sender domain: {get_sender_domain(sender)}")

    # =========================
    # 🔹 AI PREDICTION
    # =========================
    X = vectorizer.transform([clean_text(text)])
    positive_index = list(model.classes_).index(1)
    prob = float(model.predict_proba(X)[0][positive_index])
    risk = int(prob * 70)  # scale to 0-70 range

    # =========================
    # 🔹 RULE-BASED CHECKS
    # =========================

    # Keywords
    keywords = ["urgent", "verify", "login", "update", "click", "form"]
    for word in keywords:
        if word in display_text:
            reasons.add(f"Suspicious keyword: {word}")
            risk += 8

    # Links
    if "http" in display_text or "https" in display_text or ".com" in display_text or ".org" in display_text:
        reasons.add("Contains external link")
        risk += 10

    # Domains (NO DUPLICATES)
    domains = re.findall(r'\b[\w.-]+\.\w+\b', display_text)
    seen_domains = set()

    for d in domains:
        if d in seen_domains:
            continue
        seen_domains.add(d)

        # Hardcoded phishing tricks
        if "paypa1" in d or "g00gle" in d:
            reasons.add(f"Fake domain detected: {d}")
            risk += 20

        # Generic typosquatting detection
        for r in detect_typosquatting(d):
            reasons.add(r)
            risk += 15

    # Spelling mistakes (basic)
    if "loin" in display_text:
        reasons.add("Spelling mistake (possible phishing)")
        risk += 10

    # Trusted sender whitelist adjustment
    if is_trusted_sender(sender):
        risk = max(0, risk - 40)

    # =========================
    # 🔹 NORMALIZE RISK
    # =========================
    if risk > 100:
        risk = 100

    # =========================
    # 🔹 FINAL VERDICT
    # =========================
    if risk > 70:
        verdict = "Phishing"
    elif risk > 40:
        verdict = "Suspicious"
    else:
        verdict = "Safe"

    if len(reasons) == 0:
        reasons.add("No major issues detected")

    # =========================
    # 🔹 RESPONSE
    # =========================
    return jsonify({
        "risk": risk,
        "prediction": verdict,
        "probability": prob,
        "reasons": sorted(reasons)
    })


# =========================
# 🔹 RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(debug=True)