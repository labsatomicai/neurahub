import sqlite3
from flask import render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from .controllers_methods import validate_username, get_rooms, get_registered_teacher_area, get_study_areas, generate_token, degenerate_token, check_if_teacher_logged_in


# Teachers signup route

def teacher_signup_page():
    if request.method == 'POST':
        teacher_username = request.form['username']
        raw_teacher_password = request.form['password']
        area_id = request.form['area-id']

        if not validate_username(teacher_username):
            return "Invalid nickname"

        hashed_teacher_password = generate_password_hash(raw_teacher_password)

        conn = sqlite3.connect('databases/neurahub-data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO teachers (name, password, area_id) VALUES (?, ?, ?)", (teacher_username, hashed_teacher_password, area_id))
        conn.commit()
        conn.close()
        
        return redirect('/')

    study_areas = get_study_areas()
    return render_template('teacher_signup.html', areas=study_areas)

def teacher_login_page():
    if request.method == 'POST':
        inserted_teacher_username = request.form['username']
        inserted_teacher_password = request.form['password']

        if not validate_username(inserted_teacher_username):
            return "Invalid username"

        conn = sqlite3.connect('databases/neurahub-data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM teachers WHERE name = ?", (inserted_teacher_username,))
        stored_password = cursor.fetchone()

        if stored_password:
            if check_password_hash(stored_password[0], inserted_teacher_password):
                session['logged_in_teacher'] = True
                session['teacher_username'] = inserted_teacher_username
                return redirect('/teacher-panel')

        return "Login failed"
    return render_template('teacher_login.html')


def teacher_panel_page():
    if check_if_teacher_logged_in():
        username = session.get('teacher_username')
        logged_teacher_area = get_registered_teacher_area(username)

        conn = sqlite3.connect('databases/neurahub-data.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tasks.id, tasks.task_name, tasks.due_date, tasks.room_id, rooms.room_name
            FROM tasks
            LEFT JOIN rooms ON tasks.room_id = rooms.id
            WHERE tasks.teacher_username = ?
        """, (username,))
        created_tasks = cursor.fetchall()
        conn.close()

        task_summary = []

        for task in created_tasks:
            task_id, task_name, due_date, room_id, room_name = task

            task_summary.append({
                'task_id': task_id,
                'task_name': task_name,
                'due_date': due_date,
                'area_name': logged_teacher_area,
                'room_name': room_name,
                'teacher_name': username
            })

        return render_template('teacher_panel.html', created_tasks=task_summary)
    else:
        return redirect('/teacher-login')


def create_task():
    if session.get('logged_in_teacher'):
        if request.method == 'POST':
            task_name = request.form['task']
            due_date = request.form['due_date']
            area_id = request.form['area-id']
            room_id = request.form['room-id']
            creator_username = session.get('teacher_username')


            conn = sqlite3.connect('databases/neurahub-data.db')
            cursor = conn.cursor()

            cursor.execute("INSERT INTO tasks (task_name, due_date, area_id, room_id, teacher_username) VALUES (?, ?, ?, ?, ?)", (task_name, due_date, area_id, room_id, creator_username))
            conn.commit()
            conn.close()


        avaliable_study_areas = get_study_areas()
        avaliable_rooms = get_rooms()
        return render_template('create_task.html', rooms=avaliable_rooms, areas=avaliable_study_areas)


def tokenize_id(task_id):
    if session.get('logged_in_teacher'):
        token = generate_token(task_id)
        return redirect(url_for('main.return_task_edition', token=token))
    else:
        return redirect('/teacher-login')

def edit_task(token):
    if check_if_teacher_logged_in():
        original_task_id = degenerate_token(token)
        return "Ok"
    else:
        return redirect('/teacher-login')

