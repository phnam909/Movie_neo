from flask import jsonify, request, make_response
from api import app
from py2neo import NodeMatcher
from api.config.database import Database

graph = Database().connect()


# Get all movies

@app.route('/api/genres', methods=['GET'])
def getAllGenreData():
    matcher = NodeMatcher(graph)
    genre = matcher.match("Genre").limit(25).all()
    return make_response(jsonify(genre), 200)
