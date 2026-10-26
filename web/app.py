import os
import json
import urllib.request
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

# --- Google Search Console Sitemap Route ---
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

# --- Quiz Files ki list lene ke liye Route ---
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
            files = [
                item['path'].replace('Quiz/', '') 
                for item in tree_data.get('tree', []) 
                if item['path'].startswith('Quiz/') and item['path'].endswith('.json')
            ]
            return jsonify({"files": files})
    except Exception as e:
        return jsonify({"files": [], "error": str(e)})

# --- Quiz file ka data lane ka Route ---
@app.route('/api/get-quiz')
def get_quiz():
    file_path = request.args.get('path', '')
    if not file_path:
        return jsonify({"error": "No file path provided"}), 400
        
    api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/Quiz/{file_path}"
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
