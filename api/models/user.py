from py2neo import Node
from api.config.database import Database
from passlib.hash import bcrypt

graph = Database().connect()


class User:
    def __init__(self, email):
        self.email = email

    def find_by_email(self):
        user = graph.nodes.match("User", email=self.email).first()
        return user

    def register(self, name, password, admin):
        if not self.find_by_email():
            user = Node("User", email=self.email, name=name,
                        password=bcrypt.encrypt(password), admin=admin)
            graph.create(user)
            return True
        else:
            return False

    def verify_password(self, password):
        user = self.find_by_email()
        if user:
            return bcrypt.verify(password, user["password"])
        else:
            return False
