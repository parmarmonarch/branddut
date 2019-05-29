from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

with open('config.json','r') as c:
    params=json.load(c)["params"]

local_server=params['local_server']

app = Flask(__name__)
app.secret_key = 'super-secret-key'

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    CID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(1500), nullable=False)

class Posts(db.Model):
    PID = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(5000), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    image = db.Column(db.String(25), nullable=True)
    subtitle = db.Column(db.String(80), nullable=True)


@app.route("/index")
def home():
    posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
    return render_template('index.html', params=params, posts=posts)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/contact", methods = ['GET','POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')  
        entry = Contacts(name=name, phone_num=phone, email=email, message=message)
        db.session.add(entry)
        db.session.commit()

    return render_template('contact.html', params=params)

@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/dashboard", methods = ['GET','POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_username']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts = posts)

    if (request.method=='POST'):
        username = request.form.get('uname')
        password = request.form.get('pass')
        if (username == params['admin_username'] and password == params['admin_password']):
            
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts = posts)
        else:
            return render_template('login.html', params=params)

@app.route("/edit/<string:PID>", methods = ['GET','POST'])
def edit(PID):
    if ('user' in session and session['user'] == params['admin_username']):
        if (request.method == 'POST'):
            title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            content = request.form.get('content')
            slug = request.form.get('slug')
            image_file = request.form.get('image_file')
            date = datetime.now()

            if PID=='0':
                post = Posts(title=title, subtitle=subtitle, content=content,date=date, slug=slug, image=image_file)
                db.session.add(post)
                db.session.commit() 
                newpost = Posts.query.filter_by().all()[-1]
                PID = str(newpost.PID)
                return redirect('/edit/'+PID)
            else:
                post = Posts.query.filter_by(PID=PID).first()
                post.title = title
                post.subtitle = subtitle
                post.content = content
                post.date = date
                post.slug = slug
                post.image = image_file
                db.session.commit()
                return redirect('/edit/'+PID)
        post = Posts.query.filter_by(PID=PID).first()
        return render_template('edit.html', params=params,PID=PID, post=post)

@app.route("/login", methods = ['GET','POST'])
def login():
    return render_template('login.html', params=params)

app.run(debug=True)