from flask import Flask, request, redirect, render_template, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import random
import string

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:mypass@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
app.secret_key = 'secretkey'
db = SQLAlchemy(app)



#First, set up the blog so that the "add a new post" form and the blog listings are on the same page, 
#as with Get It Done!, and then separate those portions into separate routes, handler classes, and templates. 
#For the moment, when a user submits a new post, redirect them to the main blog page.

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.String(20000), nullable=False)
    date = db.Column(db.DateTime(), default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
 

    def __init__(self, title, body, author):
        self.title = title
        self.body = body
        self.author = author

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blog = db.relationship('Blog', backref='author')
    

    def __init__(self, username, password):
        self.username = username
        self.password = password


@app.before_request
def require_login():
    allowed_routes = ['login', 'blog', 'signup', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


@app.route('/')
def index():
    #join Users and Blogs basedon user ID (foreign key)
    authors = User.query.join(User.blog)
    
    return render_template('index.html', authors=authors)


@app.route('/blog', methods=['POST', 'GET'])
def blog():
    page_num = request.args.get('page_num')
    blog_id = request.args.get('id')
    user_id = request.args.get('user_id')

    if page_num:
        page_num = int(page_num)


    if user_id:
        user_blogs = Blog.query.filter_by(author_id=user_id).join(User).paginate(per_page = 5, page=page_num)
        user = User.query.filter_by(id=user_id).first()
        page_title = user.username + "'s Blogs"
        return render_template('singleUser.html', blogs=user_blogs, page_title=page_title, user=user)

    if blog_id:
        blogs = Blog.query.filter_by(id=blog_id).join(User).first()
        page_title = blogs.title
    else:
        page_title = "Build a Blog"
        blogs = Blog.query.order_by(Blog.date.desc()).join(User).paginate(per_page = 5, page=page_num)

    return render_template('blog.html', blogs=blogs, page_title=page_title)


@app.route('/newpost', methods=['POST', 'GET'])
def add_blog():
    page_title = "Add a New Post"

    if request.method == 'POST':

        blog_title = request.form['title']
        blog_body = request.form['new-blog']

        title_error=''
        blog_error = ''

        if not blog_title:
            title_error = "You need a blog title!"
        if not blog_body:
            blog_error += "You need a blog body!"

        if title_error or blog_error:
            return render_template('newpost.html', title=blog_title, body=blog_body, 
                title_error=title_error, blog_error=blog_error)
        else:
            author = User.query.filter_by(username=session['username']).first()
            new_blog = Blog(blog_title, blog_body, author) 
            db.session.add(new_blog) 
            db.session.commit()

            blog_id = str(new_blog.id)

            return redirect('/blog?id='+blog_id)

    return render_template('newpost.html', page_title=page_title)

@app.route('/signup', methods=['POST', 'GET'])
def signup():

    user_error = ''
    pass_error = ''
    ver_error = ''
    username=''
    password=''
    pass_ver=''

    if request.method == 'POST':
        
        username = request.form['username']
        password = request.form['password']
        pass_ver = request.form['verify']

        user = User.query.filter_by(username=username).first()

        if user:
            user_error = "That username already exists. Try logging in."
            username = ''
        else:
            if len(username) < 3:
                user_error = "Your username is too short. It must be longer than 3 characters."
                username = ''
            
            if len(password) < 3:
                pass_error = "Your password is too short. It must be longer than 3 characters."
            elif password != pass_ver:
                ver_error = "Your passwords do not match."
            
            if not user_error and not pass_error and not ver_error:
                encrypted_password = encrypt_password(password)
                new_user = User(username, encrypted_password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                return redirect('/blog')
            else:
                password = ''
                pass_ver = ''
                #return render_template('signup.html', username=username, password=password, verify=pass_ver, user_error=user_error, ver_error=ver_error, pass_error=pass_error)
    
    return render_template('signup.html', username=username, password=password, verify=pass_ver, user_error=user_error, ver_error=ver_error, pass_error=pass_error)

def make_salt():
    return ''.join([random.choice(string.ascii_letters) for x in range(5)])

def encrypt_password(password, salt=None):
    if not salt:
        salt = make_salt()
    hash = hashlib.sha256(str.encode(password + salt)).hexdigest()
    return '{0},{1}'.format(hash, salt)

@app.route('/login', methods=['POST', 'GET'])
def login():

    password=''
    username=''
    error=''
    
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password(password, user.password):
            session['username'] = username
            return redirect('/newpost')
        
        else:
            username=''
            password=''
            error = 'Password or username is incorrect!'

    return render_template('login.html', username=username, password=password, error=error)


def check_password(password, encrypted_password):
    salt = encrypted_password.split(',')[1]
    if encrypt_password(password, salt) == encrypted_password:
        return True
    
    return False


@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')


if __name__ == '__main__':
    app.run()