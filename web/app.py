import os
import json
import urllib.request
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

# --- TCS Exam Portal Page Route ---
@app.route('/exam')
def exam_portal():
    return render_template('exam.html')

# --- Quiz Files ki list lene ke liye Route ---
@app.route('/api/list-quizzes')
def list_quizzes():
    api_url = "https://api.github.com/repos/shreelearn23-hue/Quiz-bot/git/trees/main?recursive=1"
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            tree_data = json.loads(resp.read().decode())
            files = [
                item['path'].replace('Quiz/', '') 
                for item in tree_data.get('tree', []) 
                if item['path'].startswith('Quiz/') and item['path'].endswith('.json')
            ]
            return jsonify({"files": files})
    except Exception as e:
        return jsonify({"files": [], "error": str(e)})

# --- Telegram Bot ki JSON file fetch karne ka API Route ---
@app.route('/api/get-quiz')
def get_quiz():
    file_path = request.args.get('path', '')
    if not file_path:
        return jsonify({"error": "No file path provided"}), 400
        
    raw_url = f"https://raw.githubusercontent.com/shreelearn23-hue/Quiz-bot/main/Quiz/{file_path}"
    try:
        req = urllib.request.Request(raw_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
