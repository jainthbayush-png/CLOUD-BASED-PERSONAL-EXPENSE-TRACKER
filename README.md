# PocketWise — Cloud-Based Personal Expense Tracker

A working Flask + Firebase prototype with dashboard, transaction management, budgets and analytics.

## Stack
Python, Flask, Firebase Authentication, Cloud Firestore, HTML, CSS, JavaScript and Chart.js.

## Firebase setup
1. Create a project at https://console.firebase.google.com/.
2. In Authentication → Sign-in method, enable Email/Password.
3. Create a Cloud Firestore database.
4. Register a Web App in Project settings → General and copy its Firebase config.
5. Paste the config into `static/js/firebase-config.js`, replacing the placeholders.
6. In Project settings → Service accounts, generate a private key JSON. Save it in this folder as `serviceAccountKey.json`. Never publish this file.

## Run locally (Windows)
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000.

If the service-account file is elsewhere, set `FIREBASE_SERVICE_ACCOUNT` to its full path before running.

## Firestore structure
```text
users/{uid}/transactions/{transactionId}
users/{uid}/budgets/{YYYY-MM}
```
The Flask backend verifies each Firebase ID token and uses the verified UID to scope database operations. The Admin SDK bypasses Firestore client rules; do not expose service-account credentials. For any future direct client-side Firestore access, configure and test user-specific security rules.

## Notes
This is an academic prototype, not a banking/payment app. It does not connect to bank accounts or store card credentials. Before public deployment, use HTTPS, disable Flask debug mode, configure secrets and production logging, and review Firebase quotas and billing.
