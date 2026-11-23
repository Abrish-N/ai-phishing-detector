# Phishing Email Detector

A machine-learning phishing email detector with a Flask prediction API and a Chrome extension for Gmail.

## Features

- Trains a logistic regression classifier using TF-IDF features from email subject and body text.
- Combines the model score with rule-based checks for suspicious keywords, links, and lookalike domains.
- Returns a risk score, a verdict (`Safe`, `Suspicious`, or `Phishing`), the model probability, and detection reasons.
- Displays the result in an inline Gmail warning card.

## Dataset

The training dataset is not included in this repository because it contains email sender addresses and message bodies. To train locally, place an appropriately licensed dataset named `emails.csv` in the project directory. It must contain these columns:

```text
id, subject, sender, body, contains_link, urgent_word, suspicious_sender, label
```

The training script verifies the column names and binary labels. It trains on the combined `subject` and `body`; the other columns are dataset metadata. The expected labels are `0` (ham) and `1` (spam). The app treats class `1` as the positive phishing-risk class. The dataset and generated model files are ignored by Git.

## Requirements

- Python 3
- Flask
- Flask-CORS
- pandas
- scikit-learn

Install the Python dependencies:

```bash
pip install flask flask-cors pandas scikit-learn
```

## Run the API

From the project directory, train the model and start the Flask server:

```bash
python train_model.py
python app.py
```

Training writes `model.pkl` and `vectorizer.pkl` in the project directory. These generated artifacts are kept local and are not committed. The API listens at `http://127.0.0.1:5000`.

### Prediction endpoint

Send a JSON `POST` request to `/predict`. `subject` and `body` are combined for analysis; `sender` is optional. For compatibility, `text` can be used instead of `body`.

```json
{
  "subject": "Please verify your account",
  "body": "Review your account details.",
  "sender": "sender@example.com"
}
```

Example response:

```json
{
  "risk": 68,
  "prediction": "Suspicious",
  "probability": 0.72,
  "reasons": ["Suspicious keyword: verify"]
}
```

`risk` is the combined 0-100 score. `probability` is the model's estimated probability for class `1` (spam); the rule-based checks can change the risk and verdict independently of that probability. Requests without subject or body text receive a `400` response.

## Install the Gmail extension

1. Start the Flask API.
2. Open `chrome://extensions/` in Chrome and enable **Developer mode**.
3. Choose **Load unpacked** and select the `extensions` directory.
4. Open or reload Gmail at `https://mail.google.com/`.

The extension reads the open message's subject, body, and sender, then submits them to the local API. Keep the API running while using the extension.

## Project files

- `app.py` - Flask `/predict` API and phishing detection logic.
- `train_model.py` - dataset validation, model training, evaluation, and artifact generation.
- `check_csv.py` - validates the CSV header and row widths.
- `emails.csv` - local training dataset (not included).
- `model.pkl`, `vectorizer.pkl` - generated model and TF-IDF artifacts (not included).
- `extensions/manifest.json` - Chrome extension configuration.
- `extensions/content.js`, `extensions/style.css` - Gmail analysis and warning card.
- `templates/`, `static/` - web interface assets served at `/`.
- `APP_OVERVIEW.txt` - component and implementation overview.

## Notes

- Run commands from the project directory so `train_model.py` can locate `emails.csv`.
- Add a compatible local `emails.csv` and train the model before starting the API; the dataset and generated artifacts are intentionally not in the repository.
- Retrain the model after changing the dataset; the generated pickle files should correspond to the current training script and data.
- The trusted sender list and rule-based checks are configured in `app.py`.

## License

This project is provided as-is for learning and demonstration purposes.
