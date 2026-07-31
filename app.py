import os
from typing import Dict, List

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

LANGUAGE_TEXT = {
    "en": {
        "title": "NxtHealth AI",
        "subtitle": "Smart Rural Healthcare Assistant",
        "symptom_title": "AI Symptom Checker",
        "symptom_prompt": "Describe your symptoms and we will suggest the most likely next step.",
        "placeholder": "Example: fever for 2 days, cough, mild body pain",
        "advice": "Advice",
        "next_step": "Suggested next step",
        "severity": "Severity",
    },
    "te": {
        "title": "నెక్ట్‌హెల్త్ AI",
        "subtitle": "స్మార్ట్ రూరల్ హెల్త్‌కేర్ అసిస్టెంట్",
        "symptom_title": "AI లక్షణ పరీక్ష",
        "symptom_prompt": "మీ లక్షణాలను వివరించండి; మేము తదుపరి చర్యను సూచిస్తాము.",
        "placeholder": "ఉదాహరణ: 2 రోజులుగా జ్వరం, దగ్గు, తేలికపాటి శారీరక వాపు",
        "advice": "సలహా",
        "next_step": "సిఫార్సు చేయబడిన తదుపరి చర్య",
        "severity": "తీవ్రత",
    },
    "hi": {
        "title": "नक्स्टहेल्थ AI",
        "subtitle": "स्मार्ट ग्रामीण स्वास्थ्य सहायक",
        "symptom_title": "AI लक्षण जाँच",
        "symptom_prompt": "अपने लक्षण बताएं, हम अगला कदम सुझाएंगे।",
        "placeholder": "उदाहरण: 2 दिनों से बुखार, खांसी, हल्का शरीर दर्द",
        "advice": "सलाह",
        "next_step": "सुझाया गया अगला कदम",
        "severity": "गंभीरता",
    },
}

HOSPITALS = [
    {"name": "Rural Community Health Center", "distance": "2.4 km", "specialty": "General care"},
    {"name": "District General Hospital", "distance": "8.1 km", "specialty": "Emergency & specialists"},
    {"name": "Women & Child Care Clinic", "distance": "6.7 km", "specialty": "Mother and child care"},
]

REMINDERS = [
    {"medicine": "Paracetamol", "time": "8:00 AM", "days": "7 days"},
    {"medicine": "Vitamin C", "time": "1:00 PM", "days": "14 days"},
    {"medicine": "Blood Pressure Tablet", "time": "8:00 PM", "days": "Daily"},
]


def local_health_analysis(symptoms: str, age: int) -> Dict[str, str]:
    text = symptoms.lower()

    if any(keyword in text for keyword in ["fever", "high fever", "temperature", "cold", "cough"]) and any(keyword in text for keyword in ["breath", "difficulty", "chest pain"]):
        return {
            "diagnosis": "Possible respiratory infection or breathing issue",
            "advice": "Seek urgent medical evaluation. Rest, hydration, and avoid exertion.",
            "severity": "High",
            "next_step": "Go to the nearest emergency or urgent care center immediately.",
        }

    if any(keyword in text for keyword in ["fever", "body pain", "weakness", "headache"]) and any(keyword in text for keyword in ["cough", "cold", "sore throat"]):
        return {
            "diagnosis": "Likely viral fever or common cold",
            "advice": "Drink fluids, rest, and monitor temperature for 24-48 hours.",
            "severity": "Moderate",
            "next_step": "Visit a local clinic if symptoms worsen or last beyond 2 days.",
        }

    if any(keyword in text for keyword in ["stomach pain", "vomiting", "diarrhea", "dehydration"]):
        return {
            "diagnosis": "Possible stomach infection or dehydration",
            "advice": "Use oral rehydration salts and avoid heavy meals until stable.",
            "severity": "Moderate",
            "next_step": "Consult a doctor if severe pain, dehydration, or blood is present.",
        }

    if any(keyword in text for keyword in ["headache", "dizziness", "nausea"]) and age >= 60:
        return {
            "diagnosis": "Needs medical review, especially in older adults",
            "advice": "Monitor blood pressure, hydration, and rest. Avoid sudden exertion.",
            "severity": "Moderate",
            "next_step": "Book a consultation with a doctor within 24 hours.",
        }

    if any(keyword in text for keyword in ["rash", "allergy", "itching", "swelling"]):
        return {
            "diagnosis": "Possible allergic reaction",
            "advice": "Avoid the trigger and monitor for spread or breathing difficulty.",
            "severity": "Moderate",
            "next_step": "Seek medical help if swelling worsens or breathing becomes difficult.",
        }

    return {
        "diagnosis": "Symptoms are not specific; monitor and consult a clinician",
        "advice": "Track symptoms, hydration, and rest. Consider a routine consultation if they continue.",
        "severity": "Low",
        "next_step": "Book a checkup with a nearby clinic or community health worker.",
    }


def call_openrouter(symptoms: str, age: int, language: str) -> Dict[str, str]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return local_health_analysis(symptoms, age)

    try:
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a rural healthcare assistant. Provide brief, safe, non-diagnostic guidance in plain language. Do not claim to diagnose definitively; suggest next steps and urgency.",
                },
                {
                    "role": "user",
                    "content": f"Age: {age}\nLanguage: {language}\nSymptoms: {symptoms}\nReturn JSON with keys: diagnosis, advice, severity, next_step.",
                },
            ],
            "temperature": 0.4,
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        text = result["choices"][0]["message"]["content"]
        if "{\n" in text or "{\"" in text:
            import json
            parsed = json.loads(text)
            return {
                "diagnosis": parsed.get("diagnosis", "General health concern"),
                "advice": parsed.get("advice", "Monitor symptoms and seek care if they worsen."),
                "severity": parsed.get("severity", "Moderate"),
                "next_step": parsed.get("next_step", "Consult a medical professional."),
            }
    except Exception:
        pass

    return local_health_analysis(symptoms, age)


@app.route("/")
def home():
    return render_template("index.html", language_text=LANGUAGE_TEXT)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    symptoms = (data.get("symptoms") or "").strip()
    age = int(data.get("age") or 30)
    language = (data.get("language") or "en").lower()

    if not symptoms:
        return jsonify({"error": "Please describe your symptoms."}), 400

    analysis = call_openrouter(symptoms, age, language)
    return jsonify({
        "language": language,
        "analysis": analysis,
        "hospitals": HOSPITALS,
        "reminders": REMINDERS,
    })


@app.route("/api/hospitals")
def hospitals():
    return jsonify({"hospitals": HOSPITALS})


@app.route("/api/reminders")
def reminders():
    return jsonify({"reminders": REMINDERS})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
