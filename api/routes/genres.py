from flask import jsonify, request, make_response
from api import app
from py2neo import NodeMatcher
from api.config.database import Database

graph = Database().connect()


# Get all movies

@app.route('/api/genres', methods=['GET'])
def getAllGenreData():
    query = ('MATCH (n:Genre) RETURN {id: ID(n),name: n.name} AS genre')
    genre = graph.run(query)
    gen = genre.data()
    if gen:
        return make_response(jsonify(gen), 200)
    else:
        return make_response(jsonify({"message":"Opps! Something wrong"}),404)

@app.route('/api/genre/update/<id>', methods=['GET','PUT'])
def updateGenre(id): 
    if request.method == 'GET':
        query = ('MATCH (n:Genre) WHERE ID(n) = toInteger($id) RETURN {id: ID(n),name: n.name} AS genre')
        map = {"id": id}
        genre = graph.run(query,map)
        gen = genre.data()
        if gen:
            return make_response(jsonify(gen), 200)
        else:
            return make_response(jsonify({"message":"Opps! Something wrong"}),404)
    if request.method == 'PUT':
        name = request.form['name']
        query = ('MATCH (g:Genre)' 
                ' WHERE ID(g) = toInteger($id)' 
                ' SET g.name = $name '
                ' RETURN g ')

        map = {"id": id,"name": name}
        try:
            graph.run(query,map)
            return make_response(jsonify({"message": "success"}), 200)
        except Exception as e:
            return (str(e))
@app.route('/api/genre/delete/<id>',methods=['DELETE'])
def deleteGenre(id):
    query = ('MATCH (n:Genre) WHERE ID(n) = toInteger($id) DETACH DELETE n')
    map = {"id": id}
    try:
        graph.run(query,map)
        return make_response(jsonify({"message": "success"}), 200)
    except Exception as e:
        return (str(e))



        