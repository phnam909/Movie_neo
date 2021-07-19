from flask import jsonify, request, make_response
from api import app
from py2neo import NodeMatcher
from flask_jwt_extended import jwt_required
from api.config.database import Database
import uuid

app.secret_key = "abc"
graph = Database().connect()


# Get all movies

@app.route('/api/genres', methods=['GET'])
def getAllGenres():
    matcher = NodeMatcher(graph)
    movie = matcher.match("Genre").all()
    return make_response(jsonify(movie), 200)

# Get all movies


@app.route('/api/genres/<name>', methods=['GET'])
def getAllGenreDataTest(name):
    query = (
        'MATCH (m:Movie)<-[:IS_GENRE_OF]-(g:Genre {name: $name}) RETURN m AS movie, collect(g.name) AS genres')
    genre = graph.run(query, name=name)
    gen = genre.data()
    if gen:
        return make_response(jsonify(gen), 200)
    else:
        return make_response(jsonify({"message": "Opps! Something wrong"}), 404)


@app.route('/api/admin/genre/update/<id>', methods=['GET', 'PUT'])
@jwt_required()
def updateGenre(id):
    if request.method == 'GET':
        query = (
            'MATCH (n:Genre) WHERE ID(n) = toInteger($id) RETURN {id: ID(n),name: n.name} AS genre')
        map = {"id": id}
        genre = graph.run(query, map)
        gen = genre.data()
        if gen:
            return make_response(jsonify(gen), 200)
        else:
            return make_response(jsonify({"message": "Opps! Something wrong"}), 404)
    if request.method == 'PUT':
        name = request.form['name']
        query = ('MATCH (g:Genre)'
                 ' WHERE ID(g) = toInteger($id)'
                 ' SET g.name = $name '
                 ' RETURN g ')

        map = {"id": id, "name": name}
        try:
            graph.run(query, map)
            return make_response(jsonify({"message": "success"}), 200)
        except Exception as e:
            return (str(e))


@app.route('/api/admin/genres', methods=['GET'])
@jwt_required()
def getAdminGenres():
    matcher = NodeMatcher(graph)
    genre = matcher.match("Genre").all()
    # counter = graph.run("MATCH (g:Genre) RETURN count(g)").evaluate()
    resp = make_response(jsonify(genre), 200)
    # resp.headers['X-Total-Count'] = int(counter)
    return resp


@app.route('/api/admin/genres', methods=['POST'])
@jwt_required()
def createGenre():
    name = request.json.get("name", None)
    query = ('CREATE (g:Genre {name:$name})')
    map = {"name": name}
    try:
        graph.run(query, map)
        return make_response(jsonify({"message": "success"}), 200)
    except Exception as e:
        return (str(e))


@app.route('/api/admin/genres/<genre_name>', methods=['DELETE'])
@jwt_required()
def deleteGenre(genre_name):
    query = ('MATCH (g:Genre {name:$genre_name}) DETACH DELETE g')
    try:
        graph.run(query, genre_name=genre_name)
        return make_response(jsonify({"message": "Deleted success"}), 200)
    except Exception as e:
        return (str(e))
