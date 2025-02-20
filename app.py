import os
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv

# Activer les logs Flask et Gunicorn
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

load_dotenv()

app = Flask(__name__)

# Configuration des clés API
airtable_api_key = os.getenv("AIRTABLE_API_KEY")
airtable_base_id = os.getenv("AIRTABLE_BASE_ID")
airtable_table_name = "Pulses"
slack_signing_secret = os.getenv("SLACK_SIGNING_SECRET")

def save_to_airtable(notes, datetime_value):
    url = f"https://api.airtable.com/v0/{airtable_base_id}/{airtable_table_name}"
    headers = {
        "Authorization": f"Bearer {airtable_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "records": [
            {
                "fields": {
                    "Notes": notes,
                    "DateTime": datetime_value
                }
            }
        ]
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()

@app.route("/slack", methods=["POST"])
def slack_event():
    event_data = request.json

    # Vérifier si Slack envoie un challenge de validation
    if "challenge" in event_data:
        return jsonify({"challenge": event_data["challenge"]})
    
    if "event" in event_data:
        event = event_data["event"]
        
        if event.get("type") == "message" and "subtype" not in event:
            notes = event.get("text", "")
            datetime_value = datetime.utcfromtimestamp(float(event.get("ts", 0))).isoformat()
            save_to_airtable(notes, datetime_value)
            return jsonify({"status": "Message saved"})
    
    return jsonify({"status": "Ignored"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # Utilisation du port défini par Railway
    app.run(host="0.0.0.0", port=port)
