import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Base directories setup
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'notes')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max 16MB file upload

# -------------------------------------------------------------
# 🔐 ADMIN SECRET PASSWORD (Aap ise kabhi bhi badal sakte hain)
# -------------------------------------------------------------
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "shree123")


# -------------------------------------------------------------
# 🌐 PUBLIC FRONTEND ROUTES
# -------------------------------------------------------------

@app.route('/')
def home():
    """Main Home Page"""
    return render_template('index.html')


@app.route('/exam')
def exam():
    """CBT Mock Exam Room"""
    return render_template('exam.html')


# -------------------------------------------------------------
# 🛠️ ADMIN PANEL ROUTES (Mobile se Add karne ke liye)
# -------------------------------------------------------------

@app.route('/admin', methods=['GET'])
def admin_page():
    """Admin Dashboard UI"""
    message = request.args.get('msg')
    error = request.args.get('err')
    return render_template('admin.html', message=message, error=error)


@app.route('/admin/add-question', methods=['POST'])
def admin_add_question():
    """Directly add new MCQ question into JSON dataset"""
    admin_key = request.form.get('admin_key', '').strip()
    if admin_key != ADMIN_PASSWORD:
        return redirect(url_for('admin_page', err="चुकीचा पासवर्ड! कृपया बरोबर पासवर्ड टाका."))

    subject = request.form.get('subject', 'सामान्य ज्ञान').strip()
    question_text = request.form.get('question', '').strip()
    opt_a = request.form.get('option_a', '').strip()
    opt_b = request.form.get('option_b', '').strip()
    opt_c = request.form.get('option_c', '').strip()
    opt_d = request.form.get('option_d', '').strip()
    correct_opt = request.form.get('correct_option', 'A').strip().upper()
    explanation = request.form.get('explanation', '').strip()

    if not question_text or not opt_a or not opt_b or not opt_c or not opt_d:
        return redirect(url_for('admin_page', err="सर्व रकाने भरणे आवश्यक आहे."))

    # Target JSON dataset file
    quiz_file = os.path.join(DATA_DIR, 'quiz_questions.json')
    questions = []

    if os.path.exists(quiz_file):
        try:
            with open(quiz_file, 'r', encoding='utf-8') as f:
                questions = json.load(f)
        except Exception:
            questions = []

    new_entry = {
        "id": len(questions) + 1,
        "subject": subject,
        "question": question_text,
        "options": {
            "A": opt_a,
            "B": opt_b,
            "C": opt_c,
            "D": opt_d
        },
        "answer": correct_opt,
        "explanation": explanation
    }

    questions.append(new_entry)

    with open(quiz_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    return redirect(url_for('admin_page', msg=f"प्रश्न यशस्वीरित्या सेव्ह झाला! (एकूण प्रश्न: {len(questions)})"))


@app.route('/admin/upload-pdf', methods=['POST'])
def admin_upload_pdf():
    """Upload PDF notes directly from mobile"""
    admin_key = request.form.get('admin_key', '').strip()
    if admin_key != ADMIN_PASSWORD:
        return redirect(url_for('admin_page', err="चुकीचा पासवर्ड!"))

    if 'pdf_file' not in request.files:
        return redirect(url_for('admin_page', err="कोणतीही फाईल निवडलेली नाही."))

    file = request.files['pdf_file']
    if file.filename == '':
        return redirect(url_for('admin_page', err="कृपया एक PDF फाईल निवडा."))

    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        return redirect(url_for('admin_page', msg=f"'{filename}' PDF यशस्वीरित्या अपलोड झाली!"))
    else:
        return redirect(url_for('admin_page', err="फक्त .pdf फाईल अपलोड करता येते."))


# -------------------------------------------------------------
# ⚡ CBT EXAM API ENDPOINTS (Frontend Javascript ke liye)
# -------------------------------------------------------------

@app.route('/api/list-quizzes', methods=['GET'])
def list_quizzes():
    """Available quiz files list for CBT room"""
    available = []
    if os.path.exists(DATA_DIR):
        for fname in os.listdir(DATA_DIR):
            if fname.endswith('.json'):
                display_name = fname.replace('.json', '').replace('_', ' ').title()
                available.append({
                    "id": fname,
                    "name": display_name
                })
    return jsonify({"quizzes": available})


@app.route('/api/get-quiz', methods=['GET'])
def get_quiz():
    """Fetch 100 or specific questions for test series"""
    quiz_id = request.args.get('quiz_id', 'quiz_questions.json')
    safe_name = os.path.basename(quiz_id)
    target_path = os.path.join(DATA_DIR, safe_name)

    if not os.path.exists(target_path):
        target_path = os.path.join(DATA_DIR, 'quiz_questions.json')

    if os.path.exists(target_path):
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify({"status": "success", "questions": data})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    # Fallback dummy questions
    sample_questions = [
        {
            "id": 1,
            "subject": "मराठी व्याकरण",
            "question": "खालीलपैकी 'अमृत' या शब्दाचा समानार्थी शब्द कोणता?",
            "options": {"A": "सुधा", "B": "गरल", "C": "विष", "D": "वारुणी"},
            "answer": "A",
            "explanation": "अमृत म्हणजे सुधा किंवा पियुष."
        },
        {
            "id": 2,
            "subject": "सामान्य ज्ञान",
            "question": "महाराष्ट्राची उपराजधानी कोणती आहे?",
            "options": {"A": "पुणे", "B": "नागपूर", "C": "नाशिक", "D": "छत्रपती संभाजीनगर"},
            "answer": "B",
            "explanation": "नागपूर ही महाराष्ट्राची उपराजधानी आहे."
        }
    ]
    return jsonify({"status": "success", "questions": sample_questions})


@app.route('/api/submit-quiz', methods=['POST'])
def submit_quiz():
    """Evaluate submitted CBT test and calculate scores"""
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
        correct = q.get('answer', '').strip().upper()
        user_choice = str(user_answers.get(qid_str, '')).strip().upper()

        if not user_choice:
            skipped_count += 1
        elif user_choice == correct:
            correct_count += 1
        else:
            wrong_count += 1

    # Score calculation (1 mark per correct answer)
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
