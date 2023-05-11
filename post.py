import hashlib
import os
import traceback
import time
import arrow

local_timezone = 'Europe/Copenhagen'

def epoch_to_time_ago(epoch_time):
    return arrow.get(epoch_time).humanize(locale='da')

def epoch_to_formatted_time(epoch_time):
    return arrow.get(epoch_time).to(local_timezone).format('HH:mm:ss DD-MM-YYYY')

class Post:
    def __init__(self, connection=None, id=None, title=None, content=None, author=None, timestamp=None):
        self.connection = connection
        self.id = id
        self.title = title
        self.content = content
        self.author = author
        self.timestamp = timestamp
    def create_post(self):
        try:
            self.timestamp = int(time.time())
            self.connection.execute("""INSERT INTO posts (title, content, author, timestamp) VALUES (?,?,?,?)""",(self.title,self.content,self.author,self.timestamp))
            self.connection.commit()
            return True
        except Exception:
            traceback.print_exc()
            return False
    # Get all or posts from a specific user
    def get_posts(self, user_id=None):
        try:
            posts = []
            if user_id == None:
                posts = self.connection.execute("""SELECT posts.id,title,content,timestamp,name,lastname,picture,author FROM posts INNER JOIN users ON posts.author = users.id ORDER BY timestamp DESC;""").fetchall()
            else:
                posts = self.connection.execute("""SELECT posts.id,title,content,timestamp,name,lastname,picture,author FROM posts INNER JOIN users ON posts.author = users.id WHERE author = ? ORDER BY timestamp DESC;""",(user_id,)).fetchall()
            converted_posts = []
            for post in posts:
                post_dict = {
                    'id': post["id"],
                    'title': post["title"],
                    'content': post["content"],
                    'time_ago': epoch_to_time_ago(post["timestamp"]),
                    'formatted_time': epoch_to_formatted_time(post["timestamp"]),
                    'name': post["name"],
                    'lastname': post["lastname"],
                    'picture': post["picture"],
                    'author': post["author"]
                }
                converted_posts.append(post_dict)
            return converted_posts
        except Exception:
            traceback.print_exc()
            return False
    # Add a comment to a post
    def comment(self, user_id, comment):
        try:
            if self.id == None: return False
            timestamp = int(time.time())
            self.connection.execute("""INSERT INTO comments (post_id, user_id, comment, timestamp) VALUES (?,?,?,?)""",(self.id,user_id,comment,timestamp))
            self.connection.commit()
            return True
        except Exception:
            traceback.print_exc()
            return False

    # Get all comments from a post
    def get_comments(self):
        try:
            ## Get all comments from a post, inner join with users to get the full user object
            comments = self.connection.execute("""SELECT comments.*, users.* FROM comments INNER JOIN users ON comments.user_id = users.id WHERE post_id = ?""",(self.id,)).fetchall()
            converted_comments = []
            for comment in comments:
                comment_dict = {
                    'id': comment["id"],
                    'comment': comment["comment"],
                    'time_ago': epoch_to_time_ago(comment["timestamp"]),
                    'formatted_time': epoch_to_formatted_time(comment["timestamp"]),
                    'name': comment["name"],
                    'lastname': comment["lastname"],
                    'picture': comment["picture"],
                    'author': comment["user_id"]
                }
                converted_comments.append(comment_dict)
            return converted_comments
        except Exception:
            traceback.print_exc()
            return False
    