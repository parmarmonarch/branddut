from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug import secure_filename
from flask_mail import Mail
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import math
import json

with open('config.json','r') as c:
    params=json.load(c)["params"]

local_server=params['local_server']

app = Flask(__name__)
# Bootstrap(app)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
    )
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'userlogin'

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(40), unique=True)
    password = db.Column(db.String(80))
    relation_posts = db.relationship('Posts', cascade="save-update, merge, delete", lazy=True)
    relation_appointments = db.relationship('Appointments', cascade="save-update, merge, delete", lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(),Length(min=4, max=20)])
    password = StringField('password', validators=[InputRequired(),Length(min=8, max=80)])
    remember = BooleanField('remember_me')

class RegisterForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(),Length(min=4, max=20)])
    password = StringField('password', validators=[InputRequired(),Length(min=8, max=80)])
    email = StringField('email', validators=[InputRequired(),Length(min=8, max=40)])


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
    content2 = db.Column(db.String(100000), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    image = db.Column(db.String(25), nullable=True)
    subtitle = db.Column(db.String(80), nullable=True)
    city = db.Column(db.String(80), nullable=True)
    category = db.Column(db.String(80), nullable=True)
    id = db.Column(db.Integer, db.ForeignKey('user.id'))
    relation_featured = db.relationship('Featured', cascade="save-update, merge, delete", lazy=True)

class Featured(db.Model):
    FID = db.Column(db.Integer, primary_key=True)
    PID = db.Column(db.Integer, db.ForeignKey('posts.PID'), unique=True)
    

class Appointments(db.Model):
    AID = db.Column(db.Integer, primary_key=True)
    email_customer = db.Column(db.String(50), nullable=False)
    email_client = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    id = db.Column(db.Integer, db.ForeignKey('user.id'))
    

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
        flash('Your response has been recorded','success')

    return render_template('contact.html', params=params)

@app.route("/post/<string:post_slug>", methods = ['GET','POST'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    user = User.query.filter_by(id=post.id).first()
    if (request.method == 'POST'):
        email = request.form.get('email')
        date = request.form.get('datepicker')
        entry = Appointments(email_customer=email,email_client=user.email,date=date)
        db.session.add(entry)
        db.session.commit()
        flash('Your request has been successfully recorded','success')
        mail.send_message('New request for appointment from' + email,
            sender = params['gmail_user'],
            cc = [email],
            recipients = [user.email],
            body = 'You are requested to schedule an appointment with ' + email + '\n' + 'on ' + date)
        return render_template('post.html', params=params, post=post)
    return render_template('post.html', params=params, post=post)



@app.route("/dashboard", methods = ['GET','POST'])
def dashboard():
    users = User.query.all()
    if ('user' in session and session['user'] == params['admin_username']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts = posts, users=users)

    if (request.method=='POST'):
        username = request.form.get('uname')
        password = request.form.get('pass')
        if (username == params['admin_username'] and password == params['admin_password']):
            
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts = posts)
        
    return render_template('login.html', params=params, users=users)


@app.route("/edit/<string:PID>", methods = ['GET','POST'])
def edit(PID):
    users = User.query.filter_by().all()
    if ('user' in session and session['user'] == params['admin_username']):
        if (request.method == 'POST'):
            title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            content = request.form.get('content')
            content2 = request.form.get('content2')
            slug = request.form.get('slug')
            image_file = request.form.get('image_file')
            date = datetime.now()
            city = request.form.get('city')
            category = request.form.get('category')
            id = request.form.get('id')


            if PID=='0':
                post = Posts(title=title, subtitle=subtitle, content=content, content2=content2,date=date, slug=slug, image=image_file, city=city, category=category, id=id)
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
                post.content2 = content2
                post.date = date
                post.slug = slug
                post.image = image_file
                post.city = city
                post.category = category
                post.id = id
                db.session.commit()
                return redirect('/edit/'+PID)
        post = Posts.query.filter_by(PID=PID).first()
        return render_template('edit.html', params=params,PID=PID, post=post, users=users)



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

@app.route("/city/<string:city>/<int:page_num>", methods = ['GET','POST'])
def city(city,page_num):
    posts = Posts.query.filter_by(city=city).paginate(per_page=params['no_of_posts'], page=page_num, error_out=True)
    spost = Posts.query.filter_by(city=city).first()
    hn=posts.has_next
    hp=posts.has_prev
    nextpg = str(posts.next_num)
    if hn==False:
        nextpg = str(page_num) + "#"
    prev = str(posts.prev_num)
    if hp==False:
        prev =  str(page_num) + "#"
    # posts = Posts.query.filter_by(city=city).all()
    return render_template('city.html', params=params, posts=posts, spost=spost, nextpg=nextpg, prev=prev)

@app.route("/featured")
def featured():
    feat = db.session.query(Featured.PID)
    posts = db.session.query(Posts).filter(Posts.PID.in_(feat))
    return render_template('featured.html', params=params, posts=posts, feat=feat)

@app.route("/category/<string:category>/<int:page_num>", methods = ['GET'])
def category(category,page_num):
    posts = Posts.query.filter_by(category=category).paginate(per_page=params['no_of_posts'], page=page_num, error_out=True)
    spost = Posts.query.filter_by(category=category).first()
    hn=posts.has_next
    hp=posts.has_prev
    nextpg = str(posts.next_num)
    if hn==False:
        nextpg = str(page_num) + "#"
    prev = str(posts.prev_num)
    if hp==False:
        prev =  str(page_num) + "#"
    # posts = Posts.query.filter_by(city=city).all()
    return render_template('category.html', params=params, posts=posts, spost=spost, nextpg=nextpg, prev=prev)


@app.route("/userlogin", methods=['GET','POST'])
def userlogin():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.password == form.password.data:
                login_user(user, remember = form.remember.data)
                return redirect('/userdashboard')
            flash('The password you entered is invalid!', 'danger')
        if not user:
            flash('The Username is invalid!', 'danger')

    return render_template('userlogin.html',form=form, params=params)

@app.route("/userregister", methods=['GET','POST'])
def userregister():
    form = RegisterForm()

    if form.validate_on_submit():
        newuser = User(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(newuser)
        db.session.commit()
        flash('You have been registered successfully','success')

    return render_template('userregister.html',form=form)

@app.route("/userlogout")
@login_required
def userlogout():
    logout_user()
    return redirect('/')

@app.route("/userdashboard", methods=['GET','POST'])
@login_required
def userdashboard():
    user = User.query.filter_by(id=current_user.id).first()
    appointments = Appointments.query.filter(Appointments.id==user.id).all()
    if (request.method == 'POST'):
        if request.form.get('current_password')!=user.password:
            flash('You entered a wrong current password','danger')
        if request.form.get('current_password')==user.password:
            if request.form.get('confirm_password')==request.form.get('new_password') and len(request.form.get('new_password'))>7:
                user.password = request.form.get('new_password')
                db.session.commit()
                flash('password changed successfully','success')
            else:
                flash('password mismatch or less than 8 characters. Please retry','danger')
        if request.form.get('delpassword')==user.password:
            return redirect('/deleteuser/'+str(user.id))

    return render_template('userdashboard.html',params=params, user=user, appointments=appointments)

@app.route("/featuredadmin", methods = ['GET','POST'])
def featuredadmin():
    feat = db.session.query(Featured.PID)
    posts = db.session.query(Posts).filter(Posts.PID.in_(feat))
    addposts = Posts.query.filter(Posts.PID.notin_(feat)).all()
    if (request.method == 'POST'):
        pid = request.form.get('fid')
        entry = Featured(PID=pid)
        db.session.add(entry)
        db.session.commit()
        flash('post added to featured posts successfully','success')
    return render_template('featuredadmin.html', params=params, feat=feat, posts=posts, addposts=addposts)

@app.route("/deletefeatured/<string:PID>", methods = ['GET','POST'])
def deletefeatured(PID):
    if ('user' in session and session['user'] == params['admin_username']):
        feat = Featured.query.filter_by(PID=PID).first()
        db.session.delete(feat)
        db.session.commit()
        return redirect('/featuredadmin')

@app.route("/deleteuser/<int:id>", methods = ['GET','POST'])
def deleteuser(id):
    if ('user' in session and session['user'] == params['admin_username']):
        del_user = User.query.filter_by(id=id).first()
        db.session.delete(del_user)
        db.session.commit()
        return redirect('/')

@app.route("/deleteappointment/<int:AID>", methods = ['GET','POST'])
@login_required
def deleteappointment(AID):
    del_appointment = Appointments.query.filter_by(AID=AID).first()
    db.session.delete(del_appointment)
    db.session.commit()
    return redirect('/userdashboard')

app.run(debug=True)