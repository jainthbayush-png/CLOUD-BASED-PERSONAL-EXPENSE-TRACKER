import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, auth, firestore

app = Flask(__name__)
key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")
if not firebase_admin._apps:
    if not os.path.exists(key_path):
        raise RuntimeError("Add serviceAccountKey.json or set FIREBASE_SERVICE_ACCOUNT. See README.md.")
    firebase_admin.initialize_app(credentials.Certificate(key_path))
db = firestore.client()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        token = request.headers.get("Authorization", "")
        try:
            request.uid = auth.verify_id_token(token.split(" ", 1)[1])["uid"]
        except Exception:
            return jsonify(error="Please sign in again."), 401
        return fn(*args, **kwargs)
    return wrapped

def col(uid, name):
    return db.collection("users").document(uid).collection(name)

def clean(doc):
    x = doc.to_dict() or {}
    x["id"] = doc.id
    return x

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/data")
@login_required
def data():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    ts = [clean(d) for d in col(request.uid, "transactions").stream()]
    ts = [t for t in ts if str(t.get("date", "")).startswith(month)]
    ts.sort(key=lambda t: t.get("date", ""), reverse=True)
    income = sum(float(t["amount"]) for t in ts if t["type"] == "income")
    expenses = sum(float(t["amount"]) for t in ts if t["type"] == "expense")
    cats = {}
    for t in ts:
        if t["type"] == "expense":
            cats[t["category"]] = cats.get(t["category"], 0) + float(t["amount"])
    b = col(request.uid, "budgets").document(month).get()
    budget = float(b.to_dict().get("amount", 0)) if b.exists else 0
    return jsonify(transactions=ts, income=income, expenses=expenses, balance=income-expenses,
                   categories=cats, budget=budget, month=month)

@app.post("/api/transactions")
@login_required
def add_transaction():
    d = request.get_json() or {}
    try:
        amount = float(d["amount"])
        datetime.strptime(d["date"], "%Y-%m-%d")
        if amount <= 0 or d["type"] not in ("income", "expense") or not d["category"]:
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        return jsonify(error="Enter a valid type, amount, category and date."), 400
    record = {"type":d["type"], "amount":amount, "category":str(d["category"])[:40],
              "date":d["date"], "description":str(d.get("description",""))[:180]}
    ref = col(request.uid, "transactions").document()
    ref.set(record)
    return jsonify(id=ref.id), 201

@app.route("/api/transactions/<tid>", methods=["PUT", "DELETE"])
@login_required
def transaction(tid):
    ref = col(request.uid, "transactions").document(tid)
    if not ref.get().exists:
        return jsonify(error="Transaction not found."), 404
    if request.method == "DELETE":
        ref.delete()
        return jsonify(message="Deleted")
    d = request.get_json() or {}
    try:
        amount = float(d["amount"])
        datetime.strptime(d["date"], "%Y-%m-%d")
        if amount <= 0 or d["type"] not in ("income", "expense") or not d["category"]:
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        return jsonify(error="Please enter valid transaction details."), 400
    ref.update({"type":d["type"], "amount":amount, "category":d["category"],
                "date":d["date"], "description":str(d.get("description",""))[:180]})
    return jsonify(message="Updated")

@app.post("/api/budget")
@login_required
def budget():
    d = request.get_json() or {}
    try:
        datetime.strptime(d["month"], "%Y-%m")
        amount = float(d["amount"])
        if amount <= 0: raise ValueError()
    except (KeyError, ValueError, TypeError):
        return jsonify(error="Enter a valid month and budget amount."), 400
    col(request.uid, "budgets").document(d["month"]).set({"amount":amount})
    return jsonify(message="Budget saved")

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
