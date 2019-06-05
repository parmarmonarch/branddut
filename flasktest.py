from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug import secure_filename
import os
import math
import json

with open('config.json','r') as c:
    params=json.load(c)["params"]

local_server=params['local_server']

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']

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
    city = db.Column(db.String(80), nullable=True)
    category = db.Column(db.String(80), nullable=True)

class Featured(db.Model):
    FID = db.Column(db.Integer, primary_key=True)
    PID = db.Column(db.Integer, db.ForeignKey('posts.PID'))
    relation = db.relationship('Posts', backref=db.backref('posts', lazy=True))
    

@app.route("/")
def blogs():
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page=int(page)
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/params['no_of_posts'])
    posts = posts[(page-1)*params['no_of_posts']:(page-1)*params['no_of_posts']+params['no_of_posts']]
    #firstpage
    if page==1:
        prev = "#"
        nextpg = "/?page=" + str(page+1)
    #lastpage
    elif (page==last):
        prev = "/?page=" + str(page-1)
        nextpg = "#"
    #middlepage
    else:
        prev = "/?page=" + str(page-1)
        nextpg = "/?page=" + str(page+1)

    return render_template('index.html', params=params, posts=posts, prev=prev, nextpg=nextpg)

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



@app.route("/uploader", methods = ['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_username']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts = posts)

@app.route("/delete/<string:PID>", methods = ['GET','POST'])
def delete(PID):
    if ('user' in session and session['user'] == params['admin_username']):
        post = Posts.query.filter_by(PID=PID).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/city/<string:city>", methods = ['GET','POST'])
def city(city):
    posts = Posts.query.filter_by(city=city).all()
    return render_template('city.html', params=params, posts=posts)

@app.route("/featured")
def featured():
    feat = db.session.query(Featured.PID)
    posts = db.session.query(Posts).filter(Posts.PID.in_(feat))
    return render_template('featured.html', params=params, posts=posts, feat=feat)

app.run(debug=True)