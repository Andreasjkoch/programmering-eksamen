import hashlib
import os
import traceback
import time

class User:
    def __init__(self, connection=None, id=None, name=None, lastname=None, email=None, password=None):
        self.connection = connection
        self.id = id
        self.name = name
        self.lastname = lastname
        self.email = email
        self.password = password
    def check_password(self, password):
        if (self.password == None or self.salt == None and self.email != None):
            self.load_user()
        salt = self.salt
        plaintext = password.encode()
        digest = hashlib.pbkdf2_hmac('sha256', plaintext, salt, 10000)
        hashedPassord = digest.hex()
        if self.password == hashedPassord:
            return True
        else:
            return False
    def create_user(self):
        try:
            self.salt = os.urandom(32)
            plaintext = self.password.encode()
            digest = hashlib.pbkdf2_hmac('sha256', plaintext, self.salt, 10000)
            self.password = digest.hex()
            self.connection.execute("""INSERT INTO users (name, lastname, email, password, salt) VALUES (?,?,?,?,?)""",(self.name,self.lastname,self.email,self.password,self.salt))
            self.connection.commit()
            return True
        except Exception:
            traceback.print_exc()
            return False
    def load_user(self):
        try:
            user = None
            if self.id != None:
                user = self.connection.execute("""SELECT * FROM users WHERE id = ?""",(self.id,)).fetchall()
            elif self.email != None:
                user = self.connection.execute("""SELECT * FROM users WHERE email = ?""",(self.email,)).fetchall()
            if len(user) == 0:
                return None
            self.id = user[0]["id"]
            self.name = user[0]["name"]
            self.lastname = user[0]["lastname"]
            self.email = user[0]["email"]
            self.password = user[0]["password"]
            self.salt = user[0]["salt"]
            return user[0]
        except Exception:
            traceback.print_exc()
            return False
    def check_email(self):
        try:
            user = self.connection.execute("""SELECT * FROM users WHERE email = ?""",(self.email,)).fetchall()
            if len(user) > 0:
                return True
            else:
                return False
        except Exception:
            traceback.print_exc()
            return False
    def update_picture(self, picture):
        try:
            self.connection.execute("""UPDATE users SET picture = ? WHERE email = ?""",(picture,self.email))
            self.connection.commit()
            return True
        except Exception:
            traceback.print_exc()
            return False
    def update_banner(self, banner):
        try:
            self.connection.execute("""UPDATE users SET banner = ? WHERE email = ?""",(banner,self.email))
            self.connection.commit()
            return True
        except Exception:
            traceback.print_exc()
            return False
    def request_friend(self,friend):
        try:
            timestamp = int(time.time())
            if not (self.id): self.load_user()
            self.connection.execute("""INSERT INTO friend_requests (sender_id, receiver_id, created_at) VALUES (?,?,?)""",(self.id,friend,timestamp))
            self.connection.commit()
            return True
        except Exception:
            traceback.print_exc()
            return False
    def get_friend_status(self,friend):
        # Check if the user is already friends
        if self.id == friend: return "cancel"
        try:
            if not (self.id): self.load_user()
            friendCheck = self.connection.execute("""SELECT * FROM friendships WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)""",(self.id,friend,friend,self.id)).fetchall()
            if len(friendCheck) > 0:
                return "friends"
        except Exception:
            traceback.print_exc()
            return False
        # Check if the user has already sent a friend request
        try:
            if not (self.id): self.load_user()
            friendCheck = self.connection.execute("""SELECT * FROM friend_requests WHERE sender_id = ? AND receiver_id = ?""",(self.id,friend)).fetchall()
            if len(friendCheck) > 0:
                return "requested"
        except Exception:
            traceback.print_exc()
            return False
        # Check if the user has already received a friend request
        try:
            if not (self.id): self.load_user()
            friendCheck = self.connection.execute("""SELECT * FROM friend_requests WHERE sender_id = ? AND receiver_id = ?""",(friend,self.id)).fetchall()
            if len(friendCheck) > 0:
                return "received"
        except Exception:
            traceback.print_exc()
            return False
        return "none"
    def accept_friend(self,friend):
        try:
            if not (self.id): self.load_user()
            timestamp = int(time.time())
            self.connection.execute("""DELETE FROM friend_requests WHERE sender_id = ? AND receiver_id = ?""",(friend,self.id))
            self.connection.execute("""INSERT INTO friendships (user1_id, user2_id, created_at) VALUES (?,?,?)""",(self.id,friend,timestamp))
            self.connection.commit()
            return True
        except Exception:
            traceback.print_exc()
            return False
    def decline_friend(self,friend):
        try:
            if not (self.id): self.load_user()
            self.connection.execute("""DELETE FROM friend_requests WHERE sender_id = ? AND receiver_id = ?""",(friend,self.id))
            self.connection.commit()
            return True
        except Exception:
            traceback.print_exc()
            return False
    def cancel_friend(self,friend):
        try:
            if not (self.id): self.load_user()
            self.connection.execute("""DELETE FROM friend_requests WHERE sender_id = ? AND receiver_id = ?""",(self.id,friend))
            self.connection.commit()
            return True
        except Exception:
            traceback.print_exc()
            return False
    def remove_friend(self,friend):
        try:
            if not (self.id): self.load_user()
            self.connection.execute("""DELETE FROM friendships WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)""",(self.id,friend,friend,self.id))
            self.connection.commit()
            return True
        except Exception:
            traceback.print_exc()
            return False
    def get_friend_count(self):
        try:
            if not (self.id): self.load_user()
            friendCount = self.connection.execute("""SELECT * FROM friendships WHERE user1_id = ? OR user2_id = ?""",(self.id,self.id)).fetchall()
            return len(friendCount)
        except Exception:
            traceback.print_exc()
            return False
    def get_friends(self):
        try:
            if not (self.id): self.load_user()
            friends = self.connection.execute("""SELECT users.id, users.name, users.lastname, users.email, users.picture, users.banner FROM friendships INNER JOIN users ON friendships.user1_id = users.id OR friendships.user2_id = users.id WHERE (friendships.user1_id = ? OR friendships.user2_id = ?) AND users.id != ? ORDER BY users.name""",(self.id,self.id,self.id)).fetchall()
            if len(friends) == 0:
                return []
            return friends
        except Exception:
            traceback.print_exc()
            return False
        