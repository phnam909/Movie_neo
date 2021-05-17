from py2neo import Node
from api.config.database import Database
from passlib.hash import bcrypt
import itertools

graph = Database().connect()


class User:
    newid = itertools.count()

    def __init__(self, username):
        self.username = username
        self.id = next(User.newid)

    def find_by_username(self):
        user = graph.nodes.match("User", username=self.username).first()
        return user

    def register(self, name, password, admin, email):
        if not self.find_by_username():
            user = Node("User", id=self.id, username=self.username, name=name, email=email,
                        password=bcrypt.encrypt(password), admin=admin)
            graph.create(user)
            return True
        else:
            return False

    def verify_password(self, password):
        user = self.find_by_username()
        if user:
            return bcrypt.verify(password, user["password"])
        else:
            return False
