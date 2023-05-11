# coding=utf-8
from flask import Flask, render_template, request, url_for, redirect, make_response, session, abort
import sqlite3
import os
import time
import traceback
import base64
import io
import imghdr
from PIL import Image

from user import User
from post import Post

def make_square(img):
    width, height = img.size 
    size = min(width, height) 
    left = (width - size) // 2
    top = (height - size) // 2 
    right = (width + size) // 2 
    bottom = (height + size) // 2 
    square_img = img.crop((left, top, right, bottom)) 
    return square_img 

def compress_image(img, quality=75):
    img_io = io.BytesIO() 
    if img.mode != 'RGB':
        img = img.convert('RGB') 
    img.save(img_io, format='JPEG', quality=quality, optimize=True) 
    img_io.seek(0)
    return img_io

connection = sqlite3.connect('static/db/db.db',check_same_thread=False)
cur = connection.cursor()
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

connection.row_factory = dict_factory


def check_login(session):
    if 'session' in session and session["session"] != 0:
        try:
            email = session["session"]
            user = User(connection=connection, email=email)
            return user.load_user()
        except: return 0
    else: 
        return 0
    
app = Flask(__name__)
app.secret_key = os.urandom(64).hex()

## Error pages

@app.errorhandler(404)
def pageNotFound(e):
    user = check_login(session)
    return render_template('404.html', user=user), 404


@app.errorhandler(403)
def pageNotFound(e):
    user = check_login(session)
    return render_template('403.html', user=user), 403

## Simple functions

## Routes

@app.route('/') 
def index(): 
    user = check_login(session) 
    if user == 0: return redirect("/login")    
     
    post = Post(connection=connection) 
    posts = post.get_posts() 
    for p in posts: 
        post_id = p['id'] 
        post.id = post_id 
        post_comments = post.get_comments()  
        p['comments'] = post_comments

    friends = 0 
    if user: friends = User(connection=connection, id=user["id"]).get_friends() 
    return render_template('index.html',posts=posts, user=user, friends=friends) 
 
@app.route('/profile')
def profile():
    user = check_login(session)
    if user == 0: return redirect("/login?ref=profile")
    # Check if user is trying to view another profile
    # create a new variable for if another user has to be sent with the request'

    friends = 0
    if user: friends = User(connection=connection, id=user["id"]).get_friends()

    requestedUser = None
    if request.args.get("id"):
        requestedUser = User(connection=connection, id=request.args.get("id")).load_user()

    if requestedUser == None: requestedUser = user
    post = Post(connection=connection)
    
    posts = None
    if requestedUser != user:
        posts = post.get_posts(requestedUser["id"])
    else:
        posts = post.get_posts(user["id"])

    for p in posts:
        post_id = p['id']
        post.id = post_id
        post_comments = post.get_comments()
        p['comments'] = post_comments

    friendCount = 0
    friendCount = User(connection=connection, id=requestedUser["id"]).get_friend_count()

    friendshipStatus = User(connection=connection, id=user["id"]).get_friend_status(requestedUser["id"])

    return render_template('profile.html',posts=posts, user=user, requestedUser=requestedUser, friendshipStatus=friendshipStatus, friendCount=friendCount, friends=friends)

@app.route('/login', methods=['GET','POST'])
def login():
    ref = request.args.get("ref")
    if request.method == 'POST':
        try:
            email = request.form.get("email")
            password = request.form.get("password")
            errorMessage = 0

            user = User(connection=connection, email=email)

            if user.check_password(password):
                session['session'] = email
                if ref:
                    return redirect("/"+ref)
                else:    
                    return redirect("/")
            else:
                errorMessage = "Forkert email eller password"
                return render_template('login.html', errorMessage=errorMessage)
        except Exception:
            traceback.print_exc()
            errorMessage = "Der er sket en fejl, prøv igen"
            return render_template('login.html', errorMessage=errorMessage)
    else:
        return render_template('login.html', ref=ref)

@app.route('/register', methods=['GET','POST'])
def register():
    user = check_login(session)
    ref = request.args.get("ref")
    if request.method == 'POST':

        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmpassword = request.form.get("confirmpassword")
        
        errorPassword,errorEmail = 0,0

        if len(password) < 7: 
            errorPassword = "Dit password skal være mindst syv tegn"
        if password != confirmpassword: 
            errorPassword = "Passwords matcher ikke"
        # Check if email is already in use
        user = User(connection=connection, name=firstname, lastname=lastname, email=email, password=password)
        if user.check_email():
            errorEmail = "Email er allerede i brug"

        if not errorPassword and not errorEmail:
            if user.create_user():
                session['session'] = email
                if ref:
                    return redirect("/"+ref)
                else:    
                    return redirect("/")
            else:
                return render_template('register.html', errorPassword="Noget gik galt, prøv igen")
        else:
            return render_template('register.html', errorPassword=errorPassword, errorEmail=errorEmail)
    else:
        return render_template('register.html', ref=ref)

@app.route('/logout')
def logout():
    session['session'] = 0
    return redirect("/")

@app.route('/post/create', methods=['POST'])
def createPost():
    user = check_login(session)
    if user == 0: return abort(403)
    # get current epoch timestamp
    timestamp = int(time.time())
    title = request.form.get("title")
    content = request.form.get("content")

    ## Check if post is empty
    if title == "" or content == "":
        # return with error variable
        return redirect("/?error=Dit opslag kan ikke være tomt")
    
    ## Check if post is too long
    if len(title) > 100 or len(content) > 1000:
        # return with error variable
        return redirect("/?error=Dit opslag er for langt")
    
    post = Post(connection=connection, title=title, content=content, author=user["id"])
    post.create_post()
    return redirect("/")

@app.route('/profile/updateBanner', methods=['POST'])
def updateBanner():
    user = check_login(session)
    if user == 0: return abort(403)
    user = User(connection=connection, email=user["email"])
    banner = request.files['image']
    if imghdr.what(None, banner.read()) is None: return
    image = Image.open(banner)
    image = compress_image(image)
    ext = banner.filename.split('.')[-1]
    image = base64.b64encode(image.getvalue()).decode('utf-8')
    image_string = f'data:image/{ext};base64,{image}'

    user.update_banner(image_string)
    return redirect("/profile")

@app.route('/profile/updatePicture', methods=['POST'])
def updatePicture():
    user = check_login(session)
    if user == 0: return abort(403)
    user = User(connection=connection, email=user["email"])
    picture = request.files['image']
    if imghdr.what(None, picture.read()) is None: return
    image = Image.open(picture)
    image = make_square(image)
    image = compress_image(image)
    ext = picture.filename.split('.')[-1]
    image = base64.b64encode(image.getvalue()).decode('utf-8')
    image_string = f'data:image/{ext};base64,{image}'

    user.update_picture(image_string)
    return redirect("/profile")

@app.route('/friends/request', methods=['POST'])
def requestFriend():
    user = check_login(session)
    if user == 0: return abort(403)
    user = User(connection=connection, email=user["email"])
    friend = request.form.get("friendId")

    user.request_friend(friend)
    return redirect("/profile?id="+friend)

@app.route('/friends/cancel', methods=['POST'])
def cancelFriend():
    user = check_login(session)
    if user == 0: return abort(403)
    user = User(connection=connection, email=user["email"])
    friend = request.form.get("friendId")

    user.cancel_friend(friend)
    return redirect("/profile?id="+friend)

@app.route('/friends/accept', methods=['POST'])
def acceptFriend():
    user = check_login(session)
    if user == 0: return abort(403)
    user = User(connection=connection, email=user["email"])
    friend = request.form.get("friendId")

    user.accept_friend(friend)
    return redirect("/profile?id="+friend)

@app.route('/friends/remove', methods=['POST'])
def removeFriend():
    user = check_login(session)
    if user == 0: return abort(403)
    user = User(connection=connection, email=user["email"])
    friend = request.form.get("friendId")

    user.remove_friend(friend)
    return redirect("/profile?id="+friend)

@app.route('/friends/decline', methods=['POST'])
def declineFriend():
    user = check_login(session)
    if user == 0: return abort(403)
    user = User(connection=connection, email=user["email"])
    friend = request.form.get("friendId")

    user.decline_friend(friend)
    return redirect("/profile?id="+friend)

@app.route('/post/comment', methods=['POST'])
def commentPost():
    user = check_login(session)
    if user == 0: return abort(403)
    post = request.form.get("post_id")
    comment = request.form.get("comment")
    post = Post(connection=connection, id=post)
    post.comment(user["id"], comment)
    return redirect("/")


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

## E/R diagram af databasen
## Normalisering af data
## Class diagram
## Læs teori om normalisering af data

## Diagram over hele vores site hvordan vi bygger det objektorienteret
## Tænk over hvordan man kunne lave venneforslag, algoritmer osv.
