from flask import Flask, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:mypass@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


#First, set up the blog so that the "add a new post" form and the blog listings are on the same page, 
#as with Get It Done!, and then separate those portions into separate routes, handler classes, and templates. 
#For the moment, when a user submits a new post, redirect them to the main blog page.

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.String(20000), nullable=False)
    date = db.Column(db.DateTime(), default=datetime.utcnow)

    def __init__(self, title, body):
        self.title = title
        self.body = body
        #self.date = date


@app.route('/blog', methods=['POST', 'GET'])
def index():
    blog_id = request.args.get('id')


    if blog_id:
        blogs = Blog.query.filter_by(id=blog_id).all()
        page_title = blogs[0].title
    else:
        page_title = "Build a Blog"
        blogs = Blog.query.order_by(Blog.date.desc()).all()

    return render_template('blog.html', blogs=blogs, page_title=page_title)


@app.route('/newpost')
def add_blog():
    page_title = "Add a New Post"
    return render_template('newpost.html', page_title=page_title)

@app.route('/validate', methods=['POST', 'GET'])
def validate_blog_form():

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
        new_blog = Blog(blog_title, blog_body) 
        db.session.add(new_blog) 
        db.session.commit()

        blog_id = str(new_blog.id)

        return redirect('/blog?id='+blog_id)

@app.route('/blogz')
def individual_blog():
    blog_id = request.args.get('id')

    blog = Blog.query.filter_by(id=blog_id).all()
    

    return render_template('blogz.html', blog=blog)




if __name__ == '__main__':
    app.run()