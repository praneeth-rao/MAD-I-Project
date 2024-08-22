from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from LMS.auth import login_required
from LMS.db import get_db

bp = Blueprint('library', __name__)

@bp.route('/')
def dashboard():
    db = get_db()
    sections = db.execute(
        'SELECT sections.id, sections.name, sections.date_created, sections.description'
        ' FROM sections'
        ' ORDER BY date_created DESC'
    ).fetchall()

    if g.user == None:
        return render_template('library/home.html', sections=sections)

    if g.user['role'] == 'librarian':
        return render_template('library/librarian_dashboard.html', sections=sections)
    
    if g.user['role'] == 'user':
        return render_template('library/user_dashboard.html', sections=sections)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        db = get_db()
        error = None

        if not name:
            error = "Name should not be empty."
        elif not description:
            error = "Description should not be empty."
        
        if error:
            flash(error)
        else:
            db.execute(
                'INSERT INTO sections (name, description)'
                ' VALUES (?, ?)',
                (name, description)
            )
            db.commit()
            return redirect(url_for('library.dashboard'))
        
    return render_template('library/create_section.html')

@bp.route('/books', methods=('GET', 'POST'))
@login_required
def books():
    if request.method == 'POST':
        name = request.form['name']
        author = request.form['author']
        description = request.form['content']
        path = request.form['path']
        db = get_db()
        error = None

        section_id = request.args.get('section_id')

        if not name:
            error = 'Name should not be empty.'
        elif not author:
            error = 'author should not be empty.'
        elif not description:
            error = 'content should not be empty.'
        
        if error:
            flash(error)
        else:
            db.execute(
                'INSERT INTO books (section_id, name, description, author, path)'
                ' VALUES (?, ?, ?, ?, ?)',
                (section_id, name, description, author, path)
            )
            db.commit()
            return redirect(url_for('library.dashboard'))

    return render_template('library/add_books.html')

@bp.route('/books_view')
def books_view():
    section_id = request.args.get('section_id')
    db = get_db()
    all_books = db.execute(
        'SELECT books.id, books.name, books.author, books.description'
        ' FROM books WHERE section_id = ?',
        (section_id,)
    ).fetchall()

    in_req = db.execute(
        'SELECT user_id, book_id'
        ' FROM requests'
    ).fetchall()

    in_assign = db.execute(
        'SELECT user_id, book_id'
        ' FROM assignments'
    ).fetchall()

    temp = []
    temp1 = []
    for data in in_req:
        temp.append((data['user_id'], data['book_id']))
        temp1.append(data['user_id'])
    in_req = temp
    userids = temp1

    temp = []
    temp1 = []
    for data in in_assign:
        temp.append((data['user_id'], data['book_id']))
        temp1.append(data['user_id'])
    in_assign = temp
    userids += temp1

    return render_template('library/books_view.html', all_books=all_books, in_assign=in_assign, in_req=in_req, userids=userids)

@bp.route('/add_requests')
@login_required
def add_requests():
    book_id = request.args.get('book_id')
    db = get_db()
    db.execute(
        'INSERT INTO requests (user_id, book_id) VALUES (?, ?)',
        (g.user['id'], book_id)
    )
    db.commit()
    return redirect(url_for('library.dashboard'))

@bp.route('/assignment')
@login_required
def assignment():
    user_id = request.args.get('user_id')
    book_id = request.args.get('book_id')
    db = get_db()
    db.execute(
        'INSERT INTO assignments (user_id, book_id) VALUES (?, ?)',
        (user_id, book_id)
    )
    db.execute(
        'UPDATE assignments SET return_date = datetime(date_issued, "+7 days")'
        ' WHERE assignments.user_id = ? AND assignments.book_id = ?',
        (user_id, book_id)
    )
    request_id = request.args.get('request_id')
    db = get_db()
    db.execute(
        'DELETE FROM requests WHERE id=?',
        (request_id,)
    )
    db.commit()
    return redirect(url_for('library.dashboard'))

@bp.route('/decline')
@login_required
def decline():
    request_id = request.args.get('request_id')
    db = get_db()
    db.execute(
        'DELETE FROM requests WHERE id=?',
        (request_id,)
    )
    db.commit()
    return redirect(url_for('library.dashboard'))

@bp.route('/cancel_assignment')
@login_required
def cancel_assignment():
    assign_id = request.args.get('assign_id')
    db = get_db()
    db.execute(
        'DELETE FROM assignments WHERE id=?',
        (assign_id,)
    )
    db.commit()
    return redirect(url_for('library.dashboard'))

@bp.route('/book_return')
@login_required
def book_return():
    user_id = request.args.get('user_id')
    book_id = request.args.get('book_id')
    db = get_db()
    db.execute(
        'DELETE FROM assignments WHERE user_id=? AND book_id=?',
        (user_id, book_id)
    )
    db.commit()
    return redirect(url_for('library.dashboard'))

@bp.route('/overview')
@login_required
def overview():
    db = get_db()
    details = {}
    details['user_count'] = db.execute(
        'SELECT COUNT(role)'
        ' FROM users'
        ' WHERE role = "user"'
    ).fetchone()
    details['section_count'] = db.execute(
        'SELECT COUNT(*)'
        ' FROM sections'
    ).fetchone()
    details['book_count'] = db.execute(
        'SELECT COUNT(*)'
        ' FROM books'
    ).fetchone()
    details['request_count'] = db.execute(
        'SELECT COUNT(*)'
        ' FROM requests'
    ).fetchone()
    details['assignment_count'] = db.execute(
        'SELECT COUNT(*)'
        ' FROM assignments'
    ).fetchone()

    return render_template('library/overview.html', details=details)

@bp.route('/<int:id>/section_update', methods=('GET', 'POST'))
@login_required
def section_update(id):
    db = get_db()
    details = db.execute(
        'SELECT id, name, description'
        ' FROM sections'
        ' WHERE id = ?',
        (id,)
    ).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        error = None

        if not name:
            error = 'Name is required'
        
        if error is not None:
            flash(error)
        else:
            db.execute(
                'UPDATE sections SET name = ?, description = ?'
                ' WHERE id = ?',
                (name, description, id)
            )
            db.commit()
            return redirect(url_for('library.dashboard'))

    return render_template('library/section_update.html', details=details)

@bp.route('/<int:id>/book_update', methods=('GET', 'POST'))
@login_required
def book_update(id):
    db = get_db()
    details = db.execute(
        'SELECT id, section_id, name, description, author'
        ' FROM books'
        ' WHERE id = ?',
        (id,)
    ).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['content']
        author = request.form['author']
        error = None

        if not name:
            error = 'Name should not be empty.'
        elif not author:
            error = 'author should not be empty.'
        elif not description:
            error = 'content should not be empty.'
        
        if error is not None:
            flash(error)
        else:
            db.execute(
                'UPDATE books SET name = ?, description = ?, author = ?'
                ' WHERE id = ?',
                (name, description, author, id)
            )
            db.commit()
            return redirect(url_for('library.dashboard'))
    return render_template('library/book_update.html', details=details)

@bp.route('/<int:id>/section_delete')
@login_required
def section_delete(id):
    db = get_db()
    db.execute('DELETE FROM books WHERE section_id = ?', (id,))
    db.execute('DELETE FROM sections WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('library.dashboard'))

@bp.route('/<int:id>/book_delete')
@login_required
def book_delete(id):
    db = get_db()
    db.execute('DELETE FROM books WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('library.dashboard'))

@bp.route('/search', methods=('GET', 'POST'))
def search():
    if request.method == 'GET':
        query = request.args.get('query', '').lower()
        db = get_db()
        all_books = db.execute(
            'SELECT books.id, books.section_id, books.name, books.author, books.description'
            ' FROM books'
        ).fetchall()

        results = []
        if query != '':
            for book in all_books:
                if query in book['name'].lower() or query in book['author'].lower() or query in book['description']:
                    results.append((book['section_id'], book['id'], book['name']))
            count = len(results)
        
        if query == '':
            return redirect(url_for('library.dashboard'))

    try:    
        if g.user['role'] == 'user':
            return render_template('library/user_dashboard.html', results=results, count=count)
        elif g.user['role'] == 'librarian':
            return render_template('library/librarian_dashboard.html', results=results, count=count)
    except:
        return render_template('library/home.html', results=results, count=count)

@bp.route('/<int:id>/profile_update', methods=('GET', 'POST'))
@login_required
def profile_update(id):
    db = get_db()
    details = db.execute(
        'SELECT id, username, first_name, last_name, email, phone, address'
        ' FROM users'
        ' WHERE id = ?',
        (id,)
    ).fetchone()

    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        error = None

        if not username:
            error = 'username should not be empty.'
        
        if error is not None:
            flash(error)
        else:
            db.execute(
                'UPDATE users SET username = ?, first_name = ?, last_name = ?, email = ?, phone = ?, address = ?'
                ' WHERE id = ?',
                (username, first_name, last_name, email, phone, address, id)
            )
            db.commit()
            return redirect(url_for('library.profile_update', id = id))
    return render_template('library/profile.html', details=details)

@bp.route('/my_books', methods=('GET', 'POST'))
@login_required
def my_books():
    user_id = g.user['id']
    db = get_db()
    my_assign = db.execute(
    'SELECT assignments.id, assignments.book_id, assignments.return_date, assignments.date_issued, books.path'
    ' FROM assignments, books WHERE assignments.book_id = books.id AND assignments.user_id = ?',
    (user_id,)
    ).fetchall()

    return render_template('library/my_books.html', my_assign=my_assign)

@bp.route('/my_requests', methods=('GET', 'POST'))
@login_required
def my_requests():
    user_id = g.user['id']
    db = get_db()
    my_reqs = db.execute(
    'SELECT requests.id, requests.book_id, requests.request_date'
    ' FROM requests WHERE requests.user_id = ?',
    (user_id,)
    ).fetchall()

    return render_template('library/my_requests.html', my_reqs=my_reqs)

@bp.route('/book_requests', methods=('GET', 'POST'))
@login_required
def book_requests():
    db = get_db()
    all_reqs = db.execute(
        'SELECT requests.id, requests.user_id, requests.book_id, requests.request_date'
        ' FROM requests'
    ).fetchall()

    return render_template('library/book_requests.html', all_reqs=all_reqs)

@bp.route('/book_assignments', methods=('GET', 'POST'))
@login_required
def book_assignments():
    db = get_db()
    assigns = db.execute(
        'SELECT assignments.id, assignments.user_id, assignments.book_id, assignments.return_date, assignments.date_issued'
        ' FROM assignments'
    ).fetchall()

    return render_template('library/book_assignments.html', assigns=assigns)