import os
import json
import urllib.request
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'content_database')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/exam')
def exam_portal():
    return render_template('exam.html')

# --- GitHub API se saari JSON files dynamically dhoondhne ka route ---
@app.route('/api/list-quizzes')
def list_quizzes():
    api_url = "https://api.github.com/repos/shreelearn23-hue/Quiz-bot/git/trees/main?recursive=1"
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            tree_data = json.loads(resp.read().decode())
            # Saari JSON files ko le aayega (chahe kisi bhi folder me ho)
            files = [
                item['path']
                for item in tree_data.get('tree', [])
                if item['path'].endswith('.json') and not item['path'].startswith('.')
            ]
            return jsonify({"files": files})
    except Exception as e:
        return jsonify({"files": [], "error": str(e)})

# --- JSON file ka content download karne ka route ---
@app.route('/api/get-quiz')
def get_quiz():
    file_path = request.args.get('path', '')
    if not file_path:
        return jsonify({"error": "No file path provided"}), 400
        
    raw_url = f"https://raw.githubusercontent.com/shreelearn23-hue/Quiz-bot/main/{file_path}"
    try:
        req = urllib.request.Request(raw_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
