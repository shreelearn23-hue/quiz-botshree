import os
import json
import urllib.request
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, request, Response

app = Flask(__name__)

GH_TOKEN = os.environ.get('GH_TOKEN', '')
REPO_NAME = "shreelearn23-hue/quiz-bot"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/exam')
def exam_portal():
    return render_template('exam.html')

@app.route('/sitemap.xml')
def sitemap():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://quiz-botshree-1.onrender.com/</loc>
            <changefreq>daily</changefreq>
            <priority>1.0</priority>
        </url>
        <url>
            <loc>https://quiz-botshree-1.onrender.com/exam</loc>
            <changefreq>daily</changefreq>
            <priority>0.8</priority>
        </url>
    </urlset>"""
    return Response(xml_content.strip(), mimetype='application/xml')

# --- Private Repo se JSON files aur Commit Date (NEW tag) fetch karne ka route ---
@app.route('/api/list-quizzes')
def list_quizzes():
    api_url = f"https://api.github.com/repos/{REPO_NAME}/git/trees/main?recursive=1"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/vnd.github+json'
    }
    if GH_TOKEN:
        headers['Authorization'] = f"token {GH_TOKEN}"

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            tree_data = json.loads(resp.read().decode())
            quiz_files = []
            
            for item in tree_data.get('tree', []):
                path = item.get('path', '')
                if path.startswith('quiz/') and path.endswith('.json'):
                    relative_path = path[5:] # 'quiz/' prefix hataya
                    
                    # Free / Paid check
                    is_free = 'free' in relative_path.lower() or 'sample' in relative_path.lower()
                    
                    # Agar file ke naam ya folder me 'new' ho, ya last 5 commits me ho
                    # (Aap file naam me '_new' likh sakte hain ya system default NEW treat karega)
                    is_new = 'new' in relative_path.lower() or '2026' in relative_path.lower()

                    quiz_files.append({
                        "path": relative_path,
                        "folder": relative_path.split('/')[0] if '/' in relative_path else "General Tests",
                        "title": relative_path.split('/')[-1].replace('.json', '').replace('quiz_', '').replace('_', ' ').title(),
                        "is_paid": not is_free,
                        "is_new": is_new
                    })
                    
            return jsonify({"files": quiz_files})
    except Exception as e:
        return jsonify({"files": [], "error": str(e)})

# --- JSON file ka content download karne ka route ---
@app.route('/api/get-quiz')
def get_quiz():
    file_path = request.args.get('path', '')
    if not file_path:
        return jsonify({"error": "No file path provided"}), 400
        
    api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/quiz/{file_path}"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/vnd.github.raw+json'
    }
    if GH_TOKEN:
        headers['Authorization'] = f"token {GH_TOKEN}"

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
