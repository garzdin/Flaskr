import sqlite3
from flask import Flask, request, session, g, redirect, \
    url_for, abort, render_template, flash, jsonify
from contextlib import closing


# config
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'devkey'
USERNAME = 'admin'
PASSWORD = 'default'


# create app
app = Flask(__name__)
app.config.from_object(__name__)


# connect to db
def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


# init the db
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/')
def show_entires():
    cur = g.db.execute('select title, text from entries order by id desc')
    entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    return render_template('show_entires.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (title, text) values (?, ?)', [
            request.form['title'], request.form['text']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entires'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entires'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entires'))

@app.route('/api/posts/')
def api_posts():
    entries = g.db.execute('select id, title, text from entries order by id desc').fetchall()
    posts = []
    for entrie in entries:
        posts.append({
            'id': entrie[0],
            'post': {
                "title", entrie[1],
                "text", entrie[2]
            }
        })
    return jsonify(posts)

@app.route('/api/post/<id>')
def api_post(id):
    entrie = g.db.execute('select title, text from entries where id=' + id + ' order by id desc').fetchone()
    return jsonify(dict(title=entrie[0], text=entrie[1]))

# start app
if __name__ == '__main__':
    app.run(host='0.0.0.0')
