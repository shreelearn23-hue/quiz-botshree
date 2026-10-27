import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Base directories configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOAD_NOTES_DIR = os.path.join(os.path.dirname(__file__), 'static', 'notes')
UPLOAD_AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'static', 'audio')
MEDIA_REGISTRY_FILE = os.path.join(DATA_DIR, 'media_registry.json')

# Folders create karein agar na hon
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_NOTES_DIR, exist_ok=True)
os.makedirs(UPLOAD_AUDIO_DIR, exist_ok=True)

app.config['UPLOAD_NOTES_DIR'] = UPLOAD_NOTES_DIR
app.config['UPLOAD_AUDIO_DIR'] = UPLOAD_AUDIO_DIR
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # Max 50MB file size

# 🔐 ADMIN SECRET PASSWORD (Aap ise environment variable se ya yahan se badal sakte hain)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "shree123")


def get_stats():
    """Count uploaded exams, pdfs, audio, videos for dashboard"""
    json_count = len([f for f in os.listdir(DATA_DIR) if f.endswith('.json') and f != 'media_registry.json'])
    pdf_count = len([f for f in os.listdir(UPLOAD_NOTES_DIR) if f.endswith('.pdf')])
    audio_count = len([f for f in os.listdir(UPLOAD_AUDIO_DIR) if f.lower().endswith(('.mp3', '.m4a', '.wav'))])
    
    video_count = 0
    if os.path.exists(MEDIA_REGISTRY_FILE):
        try:
            with open(MEDIA_REGISTRY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                video_count = len(data.get('videos', []))
        except Exception:
            video_count = 0

    return {
        "json_count": json_count,
        "pdf_count": pdf_count,
        "audio_count": audio_count,
        "video_count": video_count
    }


# -------------------------------------------------------------
# 🌐 PUBLIC PAGES (Home, Exam & Smart Voice/Animation Reader)
# -------------------------------------------------------------

@app.route('/')
def home():
    """Main Home Page"""
    return render_template('index.html')


@app.route('/exam')
def exam():
    """CBT Exam Hall"""
    return render_template('exam.html')


@app.route('/read')
def read_material():
    """Smart Document Reader with Auto-Voice, Animation Hall & PDF Download"""
    topic = request.args.get('topic', 'मराठी व्याकरण - वर्णमाला व संधी')
    pdf_file = request.args.get('file', '')
    return render_template('reader.html', topic=topic, pdf_file=pdf_file)


# -------------------------------------------------------------
# 🛠️ MASTER ADMIN CONTROL PANEL
# -------------------------------------------------------------

@app.route('/admin', methods=['GET'])
def admin_page():
    message = request.args.get('msg')
    error = request.args.get('err')
    return render_template('admin.html', message=message, error=error, stats=get_stats())


# 1. DIRECT JSON EXAM PAPER UPLOAD (100 Questions / PYQs)
@app.route('/admin/upload-json-exam', methods=['POST'])
def admin_upload_json():
    admin_key = request.form.get('admin_key', '').strip()
    if admin_key != ADMIN_PASSWORD:
        return redirect(url_for('admin_page', err="चुकीचा पासवर्ड!"))

    if 'exam_file' not in request.files:
        return redirect(url_for('admin_page', err="कोणतीही JSON फाईल निवडलेली नाही."))

    file = request.files['exam_file']
    category = request.form.get('exam_category', 'general').strip()

    if file.filename == '' or not file.filename.lower().endswith('.json'):
        return redirect(url_for('admin_page', err="कृपया वैध .json फाईल निवडा."))

    filename = secure_filename(file.filename)
    final_name = f"{category}_{filename}" if not filename.startswith(category) else filename
    save_path = os.path.join(DATA_DIR, final_name)

    try:
        content = file.read().decode('utf-8')
        parsed = json.loads(content)

        # Smart format converter: agar dictionary ho toh questions nikaal lo
        if isinstance(parsed, dict):
            for key in ['questions', 'quiz', 'data', 'mcqs']:
                if key in parsed and isinstance(parsed[key], list):
                    parsed = parsed[key]
                    break

        if not isinstance(parsed, list):
            return redirect(url_for('admin_page', err="JSON फाईलमध्ये प्रश्नांची वैध यादी आढळली नाही."))

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)

        return redirect(url_for('admin_page', msg=f"अभिनंदन! '{final_name}' परीक्षा यशस्वीरित्या अपलोड झाली (एकूण प्रश्न: {len(parsed)})."))
    except Exception as e:
        return redirect(url_for('admin_page', err=f"त्रुटी: {str(e)}"))

# 2. PDF STUDY MATERIAL UPLOAD (Department-wise Mapping)
@app.route('/admin/upload-material', methods=['POST'])
def admin_upload_material():
    admin_key = request.form.get('admin_key', '').strip()
    if admin_key != ADMIN_PASSWORD:
        return redirect(url_for('admin_page', err="चुकीचा पासवर्ड!"))

    if 'pdf_file' not in request.files:
        return redirect(url_for('admin_page', err="PDF फाईल निवडलेली नाही."))

    file = request.files['pdf_file']
    dept = request.form.get('dept', 'police').strip()
    subject = request.form.get('subject', 'सामान्य ज्ञान').strip()
    title = request.form.get('title', '').strip()

    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return redirect(url_for('admin_page', err="फक्त .pdf फाईल अपलोड करता येते."))

    filename = f"{dept}_{secure_filename(file.filename)}"
    save_path = os.path.join(app.config['UPLOAD_NOTES_DIR'], filename)
    file.save(save_path)

    registry = {"pdfs": [], "audios": [], "videos": []}
    if os.path.exists(MEDIA_REGISTRY_FILE):
        try:
            with open(MEDIA_REGISTRY_FILE, 'r', encoding='utf-8') as f:
                registry = json.load(f)
        except Exception:
            pass

    registry.setdefault('pdfs', []).append({
        "dept": dept,
        "subject": subject,
        "title": title or file.filename,
        "filename": filename,
        "url": f"/static/notes/{filename}"
    })

    with open(MEDIA_REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    return redirect(url_for('admin_page', msg=f"'{title or filename}' PDF यशस्वीरित्या अपलोड होऊन {dept} विभागात जोडली गेली!"))


# 3. AUDIO / VIDEO MEDIA LECTURE HANDLER
@app.route('/admin/add-media', methods=['POST'])
def admin_add_media():
    admin_key = request.form.get('admin_key', '').strip()
    if admin_key != ADMIN_PASSWORD:
        return redirect(url_for('admin_page', err="चुकीचा पासवर्ड!"))

    media_type = request.form.get('media_type', 'video').strip()
    subject = request.form.get('subject', '').strip()
    title = request.form.get('title', '').strip()
    video_url = request.form.get('video_url', '').strip()

    registry = {"pdfs": [], "audios": [], "videos": []}
    if os.path.exists(MEDIA_REGISTRY_FILE):
        try:
            with open(MEDIA_REGISTRY_FILE, 'r', encoding='utf-8') as f:
                registry = json.load(f)
        except Exception:
            pass

    if media_type == 'video':
        if not video_url:
            return redirect(url_for('admin_page', err="कृपया व्हिडिओ लिंक (URL) टाका."))
        registry.setdefault('videos', []).append({
            "subject": subject,
            "title": title,
            "url": video_url
        })
        msg = f"व्हिडिओ व्याख्यान '{title}' यशस्वीरित्या जोडले गेले!"
    else:
        if 'audio_file' not in request.files:
            return redirect(url_for('admin_page', err="कोणतीही ऑडिओ फाईल निवडलेली नाही."))
        file = request.files['audio_file']
        if file.filename == '':
            return redirect(url_for('admin_page', err="कृपया .mp3 फाईल निवडा."))
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_AUDIO_DIR'], filename)
        file.save(save_path)
        registry.setdefault('audios', []).append({
            "subject": subject,
            "title": title or filename,
            "filename": filename,
            "url": f"/static/audio/{filename}"
        })
        msg = f"ऑडिओ फाईल '{title or filename}' यशस्वीरित्या अपलोड झाली!"

    with open(MEDIA_REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    return redirect(url_for('admin_page', msg=msg))


# -------------------------------------------------------------
# ⚡ CBT EXAM API ENDPOINTS (Frontend JS Integration)
# -------------------------------------------------------------

@app.route('/api/list-quizzes', methods=['GET'])
def list_quizzes():
    available = []
    if os.path.exists(DATA_DIR):
        for fname in os.listdir(DATA_DIR):
            if fname.endswith('.json') and fname != 'media_registry.json':
                clean_title = fname.replace('.json', '').replace('_', ' ').title()
                available.append({
                    "id": fname,
                    "name": clean_title
                })
    return jsonify({"quizzes": available})


@app.route('/api/get-quiz', methods=['GET'])
def get_quiz():
    quiz_id = request.args.get('quiz_id', 'quiz_questions.json')
    safe_name = os.path.basename(quiz_id)
    target_path = os.path.join(DATA_DIR, safe_name)

    if not os.path.exists(target_path):
        all_jsons = [f for f in os.listdir(DATA_DIR) if f.endswith('.json') and f != 'media_registry.json']
        if all_jsons:
            target_path = os.path.join(DATA_DIR, all_jsons[0])

    if os.path.exists(target_path):
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify({"status": "success", "questions": data})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "error", "message": "कोणतीही परीक्षा सापडली नाही"}), 404


@app.route('/api/submit-quiz', methods=['POST'])
def submit_quiz():
    payload = request.get_json(silent=True) or {}
    user_answers = payload.get('answers', {})
    quiz_id = payload.get('quiz_id', 'quiz_questions.json')

    safe_name = os.path.basename(quiz_id)
    target_path = os.path.join(DATA_DIR, safe_name)

    questions = []
    if os.path.exists(target_path):
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                questions = json.load(f)
        except Exception:
            questions = []

    total_questions = len(questions)
    correct_count = 0
    wrong_count = 0
    skipped_count = 0

    for q in questions:
        qid_str = str(q.get('id'))
        correct = str(q.get('answer', '')).strip().upper()
        user_choice = str(user_answers.get(qid_str, '')).strip().upper()

        if not user_choice:
            skipped_count += 1
        elif user_choice == correct:
            correct_count += 1
        else:
            wrong_count += 1

    score = correct_count
    percentage = round((score / total_questions) * 100, 2) if total_questions > 0 else 0

    return jsonify({
        "status": "success",
        "total": total_questions,
        "correct": correct_count,
        "wrong": wrong_count,
        "skipped": skipped_count,
        "score": score,
        "percentage": percentage
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
