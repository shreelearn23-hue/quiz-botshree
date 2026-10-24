import os
import json
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'content_database')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    subjects_structure = {
        "marathi_vyakaran": {
            "name": "मराठी व्याकरण",
            "topics": ["samas", "sandhi", "prayog"]
        },
        "samanya_dnyan": {
            "name": "सामान्य ज्ञान (GK)",
            "topics": ["maharashtra_bhugol", "rajyaghatana", "itihas"]
        },
        "chalu_ghadamodi": {
            "name": "चालू घडामोडी (Current Affairs)",
            "topics": ["daily_updates", "monthly_digest"]
        },
        "ganit_buddhimate": {
            "name": "अंकगणित व बुद्धिमत्ता",
            "topics": ["percentage", "profit_loss", "time_and_work"]
        }
    }
    return jsonify(subjects_structure)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
                       
