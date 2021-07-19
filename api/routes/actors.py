from flask import jsonify, request, make_response
from api import app
from py2neo import NodeMatcher
from flask_jwt_extended import jwt_required
from api.config.database import Database

app.secret_key = "abc"
graph = Database().connect()


# Get all movies

@app.route('/api/admin/actors', methods=['GET'])
@jwt_required()
def getAllActors():
    matcher = NodeMatcher(graph)
    actors = matcher.match("Actor").all()
    return make_response(jsonify(actors), 200)


@app.route('/api/admin/actors', methods=['POST'])
@jwt_required()
def createActor():
    name = request.json.get("name", None)
    query = ('CREATE (a:Actor {name:$name})')
    map = {"name": name}
    try:
        graph.run(query, map)
        return make_response(jsonify({"message": "success"}), 200)
    except Exception as e:
        return (str(e))


@app.route('/api/admin/actors/<actor_name>', methods=['DELETE'])
@jwt_required()
def deleteActor(actor_name):
    query = ('MATCH (a:Actor {name:$actor_name}) DETACH DELETE a')
    try:
        graph.run(query, actor_name=actor_name)
        return make_response(jsonify({"message": "Deleted success"}), 200)
    except Exception as e:
        return (str(e))