from flask import Flask
from api.config.database import Database
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask_cors import CORS

graph = Database().connect()

app = Flask(__name__)
CORS(app)

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=2)
jwt = JWTManager(app)


# def create_uniqueness_constraint():
#     query = "DROP CONSTRAINT ON (n:User) ASSERT n.id IS UNIQUE"
#     graph.run(query)
#
#
# create_uniqueness_constraint()

from api.routes import movies
from api.routes import genres
from api.routes import users
