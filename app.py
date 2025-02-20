import os
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


# Activer les logs Flask et Gunicorn
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

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
    
    app.logger.info(f"📤 Sending to Airtable: {data}")  # LOG AVANT ENVOI
    
    response = requests.post(url, json=data, headers=headers)
    response_json = response.json()
    
    app.logger.info(f"✅ Airtable Response: {response.status_code} - {response_json}")  # LOG REPONSE
    
    return response_json


@app.route("/slack", methods=["POST"])
def slack_event():
    event_data = request.json
    app.logger.info(f"📩 Received Slack event: {event_data}")

    if "challenge" in event_data:
        return jsonify({"challenge": event_data["challenge"]})

    if "event" in event_data:
        event = event_data["event"]

        if event.get("type") == "message":
            if "subtype" in event:
                app.logger.warning(f"⚠️ Message ignored (subtype detected): {event}")
                return jsonify({"status": "Ignored"})
            
            notes = event.get("text", "No text found")
            timestamp = float(event.get("ts", 0))
            datetime_value = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%SZ")

            app.logger.info(f"📝 Saving message: {notes}")
            response = save_to_airtable(notes, datetime_value)
            return jsonify({"status": "Message saved"})

    app.logger.warning(f"⚠️ Event ignored: {event_data}")
    return jsonify({"status": "Ignored"})



if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # Utilisation du port défini par Railway
    app.run(host="0.0.0.0", port=port)
