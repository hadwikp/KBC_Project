from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import uuid
from flask_mysqldb import MySQL
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure random key

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'         # Change to your MySQL username
app.config['MYSQL_PASSWORD'] = 'Hadwik@2006'  # Change to your MySQL password
app.config['MYSQL_DB'] = 'kbc_game'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Use dictionary cursor for query results

mysql = MySQL(app)

#Global variable to store the accepted user's unique ID
accepted_uid = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user_login', methods=['POST'])
def user_login():
    name = request.form.get('name')
    email = request.form.get('email')
    dob = request.form.get('dob')
    qualification = request.form.get('qualification')

    if not (name and email and dob and qualification):
        return "Missing fields. Please fill out all required information.", 400

    uid = uuid.uuid4().hex  # Generate a unique user ID

    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO users (uid, name, email, dob, qualification, status) VALUES (%s, %s, %s, %s, %s, 'waiting')",
        (uid, name, email, dob, qualification)
    )
    mysql.connection.commit()
    cursor.close()

    # Store the uid in the session (for initial login only)
    session['uid'] = uid
    # Redirect user to their unique waiting URL
    return redirect(url_for('waiting', uid=uid))

@app.route('/admin_login', methods=['POST'])
def admin_login():
    admin_id = request.form.get('admin_id')
    admin_password = request.form.get('admin_password')

    if admin_id == 'admin' and admin_password == 'password':
        session['admin'] = True
        return redirect(url_for('admin_page'))
    else:
        return "Invalid admin credentials", 401

@app.route('/waiting/<uid>')
def waiting(uid):
    # If a user is not logged in or the session uid doesn't match, still allow status check via URL uid.
    return render_template('waiting.html', uid=uid)

@app.route('/admin_page')
def admin_page():
    if not session.get('admin'):
        return redirect(url_for('index'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE status = 'waiting'")
    users = cursor.fetchall()
    cursor.close()

    return render_template('admin_page.html', users=users)

@app.route('/select_user', methods=['POST'])
def select_user():
    if not session.get('admin'):
        return "Unauthorized", 401

    selected_uid = request.form.get('selected_uid')
    if not selected_uid:
        return "No user selected", 400

    global accepted_uid
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE uid = %s", (selected_uid,))
    user = cursor.fetchone()
    if not user:
        return "User not found", 400

    accepted_uid = selected_uid

    # Update the database: mark the selected user as accepted and all others as rejected.
    cursor.execute("UPDATE users SET status = 'accepted' WHERE uid = %s", (selected_uid,))
    cursor.execute("UPDATE users SET status = 'rejected' WHERE uid != %s", (selected_uid,))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('admin_page'))

@app.route('/check_game_status/<uid>')
def check_game_status(uid):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT status FROM users WHERE uid = %s", (uid,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        return jsonify({'status': result['status']})
    else:
        return jsonify({'status': 'waiting'})

@app.route('/game/<uid>')
def game(uid):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT status FROM users WHERE uid = %s", (uid,))
    result = cursor.fetchone()
    cursor.close()

    if result and result['status'] == 'accepted':
        # Pass the uid to the game template so it can be used in JS
        return render_template('game.html', uid=uid)
    else:
        return redirect(url_for('not_selected'))

@app.route('/not_selected')
def not_selected():
    return render_template('not_selected.html')

# --- New Endpoints for Game Logic ---

@app.route('/get_questions/<uid>')
def get_questions(uid):
    # Verify the user is accepted
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT status FROM users WHERE uid = %s", (uid,))
    result = cursor.fetchone()
    if not result or result['status'] != 'accepted':
        cursor.close()
        return jsonify({'error': 'User not accepted'}), 403

    questions = []
    for diff in ['easy', 'medium', 'hard']:
        cursor.execute("SELECT id, question, difficulty, category, correct_answer, incorrect_answers FROM questions WHERE difficulty = %s ORDER BY RAND() LIMIT 5", (diff,))
        questions.extend(cursor.fetchall())
    cursor.close()
    return jsonify({'questions': questions})

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    question_id = data.get('question_id')
    selected_answer = data.get('selected_answer')

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT correct_answer FROM questions WHERE id = %s", (question_id,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        # Compare answers ignoring case and extra spaces.
        is_correct = (selected_answer.strip().lower() == result['correct_answer'].strip().lower())
        return jsonify({'correct': is_correct})
    else:
        return jsonify({'error': 'Invalid question id'}), 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/exit')
def exit_page():
    result = request.args.get('result', '')
    earnings = request.args.get('earnings', 0)
    return render_template('exit.html', result=result, earnings=earnings)

if __name__ == '__main__':
    app.run(debug=True)
