from flask import Flask
from api.config.database import Database

graph = Database().connect()

app = Flask(__name__)

# def create_uniqueness_constraint():
#     query = "DROP CONSTRAINT ON (n:User) ASSERT n.id IS UNIQUE"
#     graph.run(query)
#
#
# create_uniqueness_constraint()

from api.routes import movies
from api.routes import users
