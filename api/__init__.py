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
app.config['CORS_HEADERS'] = 'Content-Type'
jwt = JWTManager(app)

app.config['CORS_HEADERS'] = 'Content-Type'


cors = CORS(app, resources={r"/foo": {"origins": "http://localhost:port"}})


# def create_uniqueness_constraint():
#     query = "DROP CONSTRAINT ON (n:User) ASSERT n.id IS UNIQUE"
#     graph.run(query)
#
#
# create_uniqueness_constraint()

def create_uniqueness_constraint(label, property):
    query = "CREATE CONSTRAINT IF NOT EXISTS ON (n:{label}) ASSERT n.{property} IS UNIQUE"
    query = query.format(label=label, property = property)
    graph.run(query)

create_uniqueness_constraint('Movie','title')
create_uniqueness_constraint('Genre','name')
create_uniqueness_constraint('Actor','name')

from api.routes import movies
from api.routes import genres
from api.routes import users
from api.routes import actors
from api.routes import countries