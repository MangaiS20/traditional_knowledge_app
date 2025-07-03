from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import pytesseract
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from PIL import Image
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Path to Tesseract executable (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Mangai\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# MongoDB connection
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["traditional_knowledge"]
mongo_collection = mongo_db["ocr_annotations"]

# MySQL connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='traditional_knowledge'
    )

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM texts WHERE approved = 1")
    approved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM texts WHERE approved = 0")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM audio_links")
    audio = cursor.fetchone()[0]

    ocr = mongo_collection.count_documents({})
    
    cursor.execute("SELECT COUNT(*) FROM verse_annotations")
    verse = cursor.fetchone()[0]

    conn.close()

    stats = {
        'approved': approved,
        'pending': pending,
        'audio': audio,
        'ocr': ocr,
        'verse': verse
    }

    return render_template('index.html', stats=stats)


@app.route('/login/admin', methods=['GET', 'POST'])
def login_admin():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role='admin'", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['role'] = 'admin'
            flash('Logged in as Admin!', 'success')
            return redirect(url_for('index'))
        else:
            error = 'Invalid admin credentials'
    return render_template('login.html', error=error)

@app.route('/login/user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        username = request.form['username'].strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND role = 'user'", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['role'] = 'user'
            session['username'] = user['username']
            session['approved_features'] = user.get('approved_features', 0)
            flash('Logged in as User!', 'success')
            return redirect(url_for('index'))
        else:
            flash('User not found or not registered.', 'danger')

    return render_template('login.html')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("Username already exists.", "warning")
        else:
            cursor.execute(
                "INSERT INTO users (username, role, approved_features) VALUES (%s, 'user', 0)",
                (username,))
            conn.commit()
            flash("Registration successful. Awaiting admin approval.", "success")
        conn.close()
        return redirect(url_for('login_user'))

    return render_template('register.html')


# Admin Manage Users
@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        user_id = request.form['user_id']
        action = request.form['action']
        if action == 'approve':
            cursor.execute("UPDATE users SET approved_features = 1 WHERE id = %s", (user_id,))
            flash("User approved.", "success")
        elif action == 'reject':
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            flash("User rejected and removed.", "danger")
        conn.commit()

    cursor.execute("SELECT * FROM users WHERE role = 'user'")
    users = cursor.fetchall()
    conn.close()
    return render_template('manage_users.html', users=users)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'role' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        century = request.form['century']
        genre = request.form['genre']
        keywords = request.form['keywords']
        devanagari_text = request.form['devanagari_text']
        roman_text = request.form['roman_text']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO texts (title, author, century, genre, keywords, devanagari_text, roman_text, approved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (title, author, century, genre, keywords, devanagari_text, roman_text, 0))
        conn.commit()
        conn.close()
        flash('Record submitted for approval.', 'info')
        return redirect(url_for('index'))

    return render_template('add.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'role' not in session:
        return redirect(url_for('index'))

    results = []
    fulltext_query = ""

    if request.method == 'POST':
        # 1. Get form values
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        century = request.form.get('century', '').strip()
        genre = request.form.get('genre', '').strip()
        keywords = request.form.get('keywords', '').strip()
        script = request.form.get('script', '').strip()
        has_ocr = request.form.get('has_ocr')  # checkbox

        fulltext_query = " ".join(filter(None, [title, keywords]))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 2. Build base SQL
        sql = "SELECT * FROM texts WHERE approved = 1"
        params = []

        # 3. FULLTEXT search (title, keywords, roman_text)
        if fulltext_query:
            sql += " AND MATCH(title, keywords, roman_text) AGAINST (%s IN NATURAL LANGUAGE MODE)"
            params.append(fulltext_query)

        # 4. Other filters
        if author:
            sql += " AND author LIKE %s"
            params.append(f"%{author}%")
        if century:
            sql += " AND century LIKE %s"
            params.append(f"%{century}%")
        if genre:
            sql += " AND genre LIKE %s"
            params.append(f"%{genre}%")

        if script == "Devanagari":
            sql += " AND devanagari_text IS NOT NULL AND devanagari_text != ''"
        elif script == "Roman":
            sql += " AND roman_text IS NOT NULL AND roman_text != ''"

        # 5. OCR annotation filter
        if has_ocr:
            from pymongo import MongoClient
            mongo_client = MongoClient("mongodb://localhost:27017/")
            mongo_db = mongo_client["traditional_knowledge"]
            annotations = mongo_db["ocr_annotations"]
            annotated_files = annotations.distinct("filename")

            # Match texts whose source_file is in the annotated filenames
            if annotated_files:
                placeholders = ','.join(['%s'] * len(annotated_files))
                sql += f" AND source_file IN ({placeholders})"
                params.extend(annotated_files)

        # 6. Execute query
        cursor.execute(sql, tuple(params))
        results = cursor.fetchall()
        conn.close()

    return render_template('search.html', results=results, query=fulltext_query)

@app.route('/view')
def view():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if session.get('role') == 'admin':
        cursor.execute("SELECT * FROM texts ORDER BY id DESC")
    else:
        cursor.execute("SELECT * FROM texts WHERE approved = 1 ORDER BY id DESC")

    records = cursor.fetchall()

    for r in records:
        cursor.execute("SELECT * FROM audio_links WHERE verse_id = %s", (r['id'],))
        r['audio_links'] = cursor.fetchall()

    conn.close()
    return render_template('view.html', records=records)

@app.route('/update', methods=['GET', 'POST'])
def update():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        record_id = request.form['id']
        title = request.form['title']
        author = request.form['author']
        century = request.form['century']
        genre = request.form['genre']
        keywords = request.form['keywords']
        devanagari_text = request.form['devanagari_text']
        roman_text = request.form['roman_text']

        # Update text record
        cursor.execute("""
            UPDATE texts 
            SET title=%s, author=%s, century=%s, genre=%s, keywords=%s, devanagari_text=%s, roman_text=%s 
            WHERE id=%s
        """, (title, author, century, genre, keywords, devanagari_text, roman_text, record_id))

        # Update audio if exists
        audio_id = request.form.get('audio_id')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        audio_description = request.form.get('audio_description')
        file = request.files.get('audio')

        if audio_id:
            if file and file.filename:
                filename = secure_filename(file.filename)
                audio_dir = os.path.join('static', 'audio')
                os.makedirs(audio_dir, exist_ok=True)
                file_path = os.path.join(audio_dir, filename)
                file.save(file_path)
                relative_path = f"audio/{filename}"

                cursor.execute("""
                    UPDATE audio_links
                    SET file_path=%s, start_time=%s, end_time=%s, audio_description=%s
                    WHERE id=%s
                """, (relative_path, start_time, end_time, audio_description, audio_id))
            else:
                cursor.execute("""
                    UPDATE audio_links
                    SET start_time=%s, end_time=%s, audio_description=%s
                    WHERE id=%s
                """, (start_time, end_time, audio_description, audio_id))

        conn.commit()
        flash('Record updated successfully.', 'success')
        return redirect(url_for('update'))

    # Load text + audio together
    cursor.execute("""
        SELECT t.*, a.id AS audio_id, a.file_path, a.start_time, a.end_time, a.audio_description
        FROM texts t
        LEFT JOIN audio_links a ON t.id = a.verse_id
        ORDER BY t.id DESC
    """)
    records = cursor.fetchall()
    conn.close()

    return render_template('update.html', records=records)

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM texts ORDER BY id DESC")
    records = cursor.fetchall()

    if request.method == 'POST':
        record_id = request.form['id']
        cursor.execute("DELETE FROM texts WHERE id = %s", (record_id,))
        conn.commit()
        flash('Record deleted successfully.', 'warning')
        return redirect(url_for('delete'))

    conn.close()
    return render_template('delete.html', records=records)

@app.route('/approve', methods=['GET', 'POST'])
def approve():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        record_id = request.form['id']
        action = request.form['action']

        if action == 'approve':
            cursor.execute("UPDATE texts SET approved = 1 WHERE id = %s", (record_id,))
            flash('Record approved successfully.', 'success')
        elif action == 'reject':
            cursor.execute("DELETE FROM texts WHERE id = %s", (record_id,))
            flash('Record rejected and removed.', 'danger')

        conn.commit()

    cursor.execute("SELECT * FROM texts WHERE approved = 0")
    records = cursor.fetchall()
    conn.close()

    return render_template('approve.html', records=records)

import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from PIL import Image
import os
import pytesseract

# Mongo + MySQL connection assumed pre-defined
# mongo_collection = ...
# get_db_connection = ...

# --- OCR IMAGE UPLOAD + MySQL linkage ---
@app.route('/ocr', methods=['GET', 'POST'])
def ocr():
    if request.method == 'POST':
        file = request.files.get('image')
        if not file or file.filename == '':
            flash('No image uploaded.', 'danger')
            return redirect(url_for('ocr'))

        filename = secure_filename(file.filename)
        upload_path = os.path.join('uploads', filename)
        file.save(upload_path)

        image = Image.open(upload_path)
        extracted_text = pytesseract.image_to_string(image, lang='eng+hin+tam+san')

        # Save OCR to Mongo
        mongo_collection.insert_one({'filename': filename, 'text': extracted_text})

        # Link in SQL with source_file
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO texts (title, author, century, genre, keywords, devanagari_text, roman_text, approved, source_file)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s)
        """, ("", "", "", "", "", "", "", filename))
        conn.commit()
        conn.close()

        flash('OCR complete. Text saved to MongoDB and linked in MySQL.', 'success')
        return redirect(url_for('view_annotations'))

    return render_template('ocr.html')

# --- OCR Annotation Interface ---
@app.route('/ocr_annotate', methods=['GET', 'POST'])
def ocr_annotate():
    if request.method == 'POST':
        manuscript_id = request.form['manuscript_id']
        ocr_text = request.form['ocr_text']
        comment = request.form['comment']

        mongo_collection.insert_one({
            'manuscript_id': manuscript_id,
            'ocr_text': ocr_text,
            'comment': comment
        })

        flash("OCR Annotation saved!", "success")
        return redirect(url_for('ocr_annotate'))

    return render_template('ocr_annotate.html')

# --- VIEW OCR Annotations (MongoDB) ---
@app.route('/annotations')
def view_annotations():
    annotations = mongo_collection.find().sort("_id", -1)
    return render_template('annotation.html', annotations=annotations)

@app.route('/ocr_link', methods=['GET', 'POST'])
def ocr_link():
    if session.get('role') not in ['admin', 'user'] or not session.get('approved_features'):
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, title, source_file FROM texts WHERE approved = 1")
    records = cursor.fetchall()

    if request.method == 'POST':
        record_id = request.form['record_id']
        file = request.files['image']

        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join('uploads', filename)
            file.save(filepath)

            # Extract OCR text
            image = Image.open(filepath)
            extracted_text = pytesseract.image_to_string(image, lang='eng+hin+san+tam')

            # Save to MongoDB
            mongo_collection.insert_one({'filename': filename, 'text': extracted_text})

            # ✅ UPDATE the record in MySQL to store the source file
            cursor.execute("UPDATE texts SET source_file = %s WHERE id = %s", (filename, record_id))
            conn.commit()

            flash("OCR uploaded and linked to text!", "success")
            return redirect(url_for('ocr_link'))

    # 👇 Add OCR text to display if available
    for record in records:
        record['ocr_text'] = None
        if record.get('source_file'):
            ocr = mongo_collection.find_one({'filename': record['source_file']})
            if ocr:
                record['ocr_text'] = ocr.get('text')

    conn.close()
    return render_template('ocr_link.html', records=records)


# --- AUDIO LINK TO VERSE ---
@app.route('/audio_link', methods=['GET', 'POST'])
def audio_link():
    if session.get('role') not in ['admin', 'user'] or not session.get('approved_features'):
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, title FROM texts WHERE approved = 1")
    verses = cursor.fetchall()

    if request.method == 'POST':
        verse_id = request.form['verse_id']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        audio_description = request.form.get('audio_description', '')
        file = request.files['audio']

        if file and file.filename:
            filename = secure_filename(file.filename)
            audio_dir = os.path.join('static', 'audio')
            os.makedirs(audio_dir, exist_ok=True)
            full_path = os.path.join(audio_dir, filename)
            file.save(full_path)

            relative_path = f"audio/{filename}"
            cursor.execute("""
                INSERT INTO audio_links (verse_id, file_path, start_time, end_time, audio_description)
                VALUES (%s, %s, %s, %s, %s)
            """, (verse_id, relative_path, start_time, end_time, audio_description))
            conn.commit()
            flash("Audio linked to verse!", "success")
            return redirect(url_for('audio_link'))

    conn.close()
    return render_template('audio_upload.html', verses=verses)

# --- SANSKRIT VERSE ANNOTATION ---
@app.route('/annotate', methods=['GET', 'POST'])
def annotate():
    if 'role' not in session:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, title, devanagari_text, roman_text FROM texts WHERE approved = 1")
    verses = cursor.fetchall()

    if request.method == 'POST':
        text_id = int(request.form['text_id'])
        script = request.form['script']

        cursor.execute("SELECT * FROM verse_annotations WHERE text_id = %s AND script_type = %s", (text_id, script))
        if cursor.fetchone():
            flash("Annotation already exists for this script and verse.", "warning")
            return redirect(url_for('annotate'))

        annotations = {}
        index = 0
        while True:
            line = request.form.get(f'line_{index}')
            note = request.form.get(f'note_{index}')
            if line is None:
                break
            annotations[line] = note
            index += 1

        cursor.execute("""
            INSERT INTO verse_annotations (text_id, script_type, annotations)
            VALUES (%s, %s, %s)
        """, (text_id, script, json.dumps(annotations)))
        conn.commit()
        conn.close()

        flash("Annotation saved successfully!", "success")
        return redirect(url_for('annotate'))

    conn.close()
    return render_template('annotate.html', verses=verses)

# --- VIEW SAVED VERSE ANNOTATIONS (SQL) ---
@app.route('/view_verse_annotations')
def view_verse_annotations():
    if 'role' not in session:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT va.*, t.title
        FROM verse_annotations va
        JOIN texts t ON va.text_id = t.id
        ORDER BY va.created_at DESC
    """)
    annotations = cursor.fetchall()
    conn.close()

    for ann in annotations:
        ann['annotations'] = json.loads(ann['annotations'])

    return render_template('verse_annotations.html', annotations=annotations)

# --- DELETE VERSE ANNOTATION ---
@app.route('/delete_annotation/<int:id>', methods=['POST'])
def delete_annotation(id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM verse_annotations WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    flash("Annotation deleted successfully.", "danger")
    return redirect(url_for('view_verse_annotations'))

@app.route('/view_linked_ocr', methods=['POST'])
def view_linked_ocr():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    filename = request.form['filename']
    result = mongo_collection.find_one({'filename': filename})

    if not result:
        flash("No OCR text found for this file.", "warning")
        return redirect(url_for('ocr_link'))

    return render_template('view_linked_ocr.html', result=result)



@app.route('/view_audio')
def view_audio():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT a.*, t.title 
        FROM audio_links a
        JOIN texts t ON a.verse_id = t.id
        ORDER BY a.id DESC
    """)
    audios = cursor.fetchall()
    conn.close()

    return render_template('audio_list.html', audios=audios)
@app.route('/delete_audio/<int:id>', methods=['POST'])
def delete_audio(id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get file path to delete audio file from disk
    cursor.execute("SELECT file_path FROM audio_links WHERE id = %s", (id,))
    result = cursor.fetchone()
    if result:
        filepath = os.path.join('static', result[0])
        if os.path.exists(filepath):
            os.remove(filepath)

    # Delete from DB
    cursor.execute("DELETE FROM audio_links WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    flash("Audio deleted successfully.", "danger")
    return redirect(url_for('view_audio'))
@app.route('/edit_audio/<int:id>', methods=['GET', 'POST'])
def edit_audio(id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        description = request.form['audio_description']

        cursor.execute("""
            UPDATE audio_links 
            SET start_time = %s, end_time = %s, audio_description = %s
            WHERE id = %s
        """, (start_time, end_time, description, id))
        conn.commit()
        conn.close()

        flash("Audio details updated!", "success")
        return redirect(url_for('view_audio'))

    # GET request: load current audio details
    cursor.execute("SELECT * FROM audio_links WHERE id = %s", (id,))
    audio = cursor.fetchone()
    conn.close()

    return render_template('edit_audio.html', audio=audio)


#extract metadata
import fitz  # PyMuPDF

@app.route('/extract_metadata', methods=['GET', 'POST'])
def extract_metadata():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    extracted_data = {}

    if request.method == 'POST':
        file = request.files['image']
        if file and file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join('uploads', filename)
            file.save(path)

            text = ""
            try:
                if filename.lower().endswith(".pdf"):
                    doc = fitz.open(path)
                    for page in doc:
                        text += page.get_text()
                else:
                    image = Image.open(path)
                    text = pytesseract.image_to_string(image, lang='san+eng+hin')
            except Exception as e:
                flash(f"Error processing file: {e}", "danger")
                return redirect(url_for('extract_metadata'))

            # Clean and parse
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            full_text = "\n".join(lines)

            import re
            for line in lines:
                line_lower = line.lower()

                if re.search(r'\btitle\b', line_lower) and 'title' not in extracted_data:
                    extracted_data['title'] = re.sub(r'.*title[:=\-–]?\s*', '', line, flags=re.IGNORECASE).strip()
                elif re.search(r'\bauthor\b|\bby\b', line_lower) and 'author' not in extracted_data:
                    extracted_data['author'] = re.sub(r'.*(author|by)[:=\-–]?\s*', '', line, flags=re.IGNORECASE).strip()
                elif 'century' in line_lower and 'century' not in extracted_data:
                    extracted_data['century'] = re.sub(r'.*century[:=\-–]?\s*', '', line, flags=re.IGNORECASE).strip()
                elif 'genre' in line_lower and 'genre' not in extracted_data:
                    extracted_data['genre'] = re.sub(r'.*genre[:=\-–]?\s*', '', line, flags=re.IGNORECASE).strip()
                elif 'keyword' in line_lower and 'keywords' not in extracted_data:
                    extracted_data['keywords'] = re.sub(r'.*keywords?[:=\-–]?\s*', '', line, flags=re.IGNORECASE).strip()
                elif 'devanagari' in line_lower and 'devanagari_text' not in extracted_data:
                    extracted_data['devanagari_text'] = re.sub(r'.*devanagari\s*text[:=\-–]?\s*', '', line, flags=re.IGNORECASE).strip()
                elif re.match(r'^[\u0900-\u097F\s।॥]+$', line) and 'devanagari_text' not in extracted_data:
                    extracted_data['devanagari_text'] = line.strip()
                elif 'roman text' in line_lower and 'roman_text' not in extracted_data:
                    extracted_data['roman_text'] = re.sub(r'.*roman\s*text[:=\-–]?\s*', '', line, flags=re.IGNORECASE).strip()
                elif any(c in line for c in ['ā', 'ī', 'ṭ', 'ṇ', 'ś', 'ṃ']) and 'roman_text' not in extracted_data:
                    extracted_data['roman_text'] = line.strip()

            # Add smart guesses for genre and keywords
            if 'ramayan' in full_text.lower():
                extracted_data['genre'] = "Epic / Itihasa"
                extracted_data['keywords'] = "Ramayana, Rama, Sita, Valmiki"
            elif 'gita' in full_text.lower():
                extracted_data['genre'] = "Spiritual / Philosophy"
                extracted_data['keywords'] = "Krishna, Arjuna, Dharma, Karma"

            return render_template('verify_metadata.html', data=extracted_data)

    return render_template('extract_upload.html')


# User extract
import fitz  # PyMuPDF

@app.route('/user_extract_metadata', methods=['GET', 'POST'])
def user_extract_metadata():
    if session.get('role') != 'user':
        return redirect(url_for('index'))

    extracted_data = {}

    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join('uploads', filename)
            file.save(filepath)

            text = ""
            try:
                if filename.lower().endswith(".pdf"):
                    doc = fitz.open(filepath)
                    for page in doc:
                        text += page.get_text()
                else:
                    image = Image.open(filepath)
                    text = pytesseract.image_to_string(image, lang='san+eng+hin')
            except Exception as e:
                flash(f"Error processing file: {e}", "danger")
                return redirect(url_for('user_extract_metadata'))

            # Process lines as before
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            full_text = "\n".join(lines)

            extracted_data['title'] = " ".join(lines[0:3])
            for line in lines:
                if re.search(r'valmiki|author|by', line, re.IGNORECASE):
                    extracted_data['author'] = line
                    break
            else:
                extracted_data['author'] = "Unknown"

            if "ramayan" in full_text.lower():
                extracted_data['genre'] = "Epic Poetry / Hindu Scripture / Itihasa (History)"
                extracted_data['keywords'] = "Ramayana, Sita, Rama, Hanuman, Dharma"
            elif "gita" in full_text.lower():
                extracted_data['genre'] = "Spiritual Text / Bhagavad Gita"
                extracted_data['keywords'] = "Krishna, Arjuna, Dharma, Moksha"
            else:
                extracted_data['genre'] = "Indic Literature"
                extracted_data['keywords'] = "Sanskrit, Sloka, Indic Text"

            devanagari = [l for l in lines if re.match(r'^[\u0900-\u097F\s।॥]+$', l)]
            extracted_data['devanagari_text'] = "\n".join(devanagari[:5])

            roman = [l for l in lines if any(c in l for c in ['ā', 'ī', 'ṭ', 'ḍ', 'ṃ', 'ś', 'ṛ'])]
            extracted_data['roman_text'] = "\n".join(roman[:5])

            return render_template('verify_metadata.html', data=extracted_data)

    return render_template('extract_upload.html')




from flask import jsonify

@app.route('/api/texts', methods=['GET'])
def api_texts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Collect filters from URL params
    title = request.args.get('title', '')
    author = request.args.get('author', '')
    century = request.args.get('century', '')
    genre = request.args.get('genre', '')
    keywords = request.args.get('keywords', '')

    sql = "SELECT * FROM texts WHERE approved = 1"
    params = []

    if title:
        sql += " AND title LIKE %s"
        params.append(f"%{title}%")
    if author:
        sql += " AND author LIKE %s"
        params.append(f"%{author}%")
    if century:
        sql += " AND century LIKE %s"
        params.append(f"%{century}%")
    if genre:
        sql += " AND genre LIKE %s"
        params.append(f"%{genre}%")
    if keywords:
        sql += " AND keywords LIKE %s"
        params.append(f"%{keywords}%")

    cursor.execute(sql, tuple(params))
    results = cursor.fetchall()
    conn.close()

    return jsonify(results)

import re
from markupsafe import Markup

@app.template_filter('highlight')
def highlight(text, query):
    if not text or not query:
        return text
    try:
        keywords = query.split()
        for word in keywords:
            text = re.sub(f'(?i)({re.escape(word)})', r'<mark>\1</mark>', text)
        return Markup(text)
    except Exception:
        return text

import csv
import io
import json
from flask import Response, send_file
from fpdf import FPDF

import io
import csv
import json
from flask import Response, send_file
from fpdf import FPDF
from datetime import datetime

from flask import Response, send_file
from fpdf import FPDF
import io
import json
import csv

@app.route('/export/<format>')
def export_data(format):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM texts WHERE approved = 1")
    records = cursor.fetchall()
    conn.close()

    if not records:
        return "No approved records to export", 404

    # ✅ JSON Export
    if format == 'json':
        response = app.response_class(
            response=json.dumps(records, ensure_ascii=False, indent=2, default=str),
            mimetype='application/json'
        )
        response.headers["Content-Disposition"] = "attachment; filename=approved_texts.json"
        return response

    # ✅ CSV Export
    elif format == 'csv':
        output = io.StringIO()
        fieldnames = records[0].keys() if records and records[0] else []
        if not fieldnames:
            return "No valid data to export as CSV.", 400
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment;filename=approved_texts.csv"}
        )


    # ✅ PDF Export
    elif format == 'pdf':
        pdf = FPDF()
        pdf.add_page()

        try:
            pdf.add_font("NotoSans", "", "NotoSansDevanagari-Regular.ttf", uni=True)
            pdf.set_font("NotoSans", size=12)
        except Exception as e:
            return f"Font file error: {e}", 500

        for i, record in enumerate(records, start=1):
            pdf.set_font("NotoSans", size=12)
            pdf.cell(0, 10, f"📄 Record #{i}", ln=True)

            for key, value in record.items():
                value = "" if value is None else str(value)
                pdf.set_font("NotoSans", size=11)
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(0, 8, f"{key.title()}: {value}")

            pdf.ln(4)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(6)

        output = io.BytesIO()
        pdf_output = pdf.output(dest='S').encode('latin1')
        output.write(pdf_output)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="approved_texts.pdf",
            mimetype="application/pdf"
        )

    # ❌ Unsupported
    return "Unsupported format. Use json, csv, or pdf.", 400



@app.route('/export/ocr_annotations')
def export_ocr_annotations():
    annotations = list(mongo_collection.find())
    if not annotations:
        return "No OCR annotations to export.", 404

    # Convert ObjectId to string
    for ann in annotations:
        ann['_id'] = str(ann['_id'])

    response = app.response_class(
        response=json.dumps(annotations, ensure_ascii=False, indent=2),
        mimetype='application/json'
    )
    response.headers["Content-Disposition"] = "attachment; filename=ocr_annotations.json"
    return response

from datetime import datetime

@app.route('/export/verse_annotations')
def export_verse_annotations():
    if 'role' not in session or session.get('role') != 'admin':
        flash("Access denied", "danger")
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT va.id, va.script_type, va.annotations, va.created_at, t.title 
        FROM verse_annotations va
        JOIN texts t ON va.text_id = t.id
    """)
    data = cursor.fetchall()
    conn.close()

    for item in data:
        # Parse JSON annotations
        try:
            item['annotations'] = json.loads(item['annotations'])
        except:
            item['annotations'] = {}

        # Convert datetime to string
        if isinstance(item.get('created_at'), datetime):
            item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')

    return Response(
        response=json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json',
        headers={"Content-Disposition": "attachment; filename=verse_annotations.json"}
    )



if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
