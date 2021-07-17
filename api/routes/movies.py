from flask import jsonify, request, make_response, flash
from api import app
from flask_jwt_extended import jwt_required
from py2neo import NodeMatcher
from api.config.database import Database
from werkzeug.utils import secure_filename
from slugify import slugify
from datetime import datetime
import calendar
import time
import uuid
import os

app.secret_key = "abc"
graph = Database().connect()

# ===================== Admin router  ============================
# Get all
# @app.route('/api/admin/movies', methods=['GET'])
# @jwt_required()
# def getAllMovieAdmin():
#     matcher = NodeMatcher(graph)
#     movie = matcher.match("Movie").all()
#     resp = make_response(jsonify(movie), 200)
#     return resp
@app.route('/api/admin/movies', methods=['GET'])
@jwt_required()
def getAllMovieAdmin():
    query = (
        'MATCH (c:Country)<-[:PRODUCTED_BY]-(m:Movie)<-[:IS_GENRE_OF]-(g:Genre) RETURN m AS movie, collect(g.name) AS genres, c.country AS country ORDER BY m.timestamp DESC')
    genre = graph.run(query)
    gen = genre.data()
    if gen:
        return make_response(jsonify(gen), 200)
    else:
        return make_response(jsonify({"message": "Opps! Something wrong"}), 404)

# Count

@app.route('/api/admin/count', methods=['GET'])
@jwt_required()
def getAllCount():
    counter = graph.run("MATCH (m:Movie) "
                        "RETURN {label: 'Movies', url:'/movies', count: count(m)} as info "
                        "UNION ALL "
                        "MATCH (u:User) "
                        "RETURN {label: 'Users', url:'/users', count: count(u)} as info "
                        "UNION ALL "
                        "MATCH (g:Genre) "
                        "RETURN {label: 'Genres', url:'/genres', count: count(g)} as info").data()
    resp = make_response(jsonify(counter), 200)
    return resp

# Get one


@app.route('/api/admin/movies/<id>', methods=['GET'])
@jwt_required()
def getMovieDataAdmin(id):
    matcher = NodeMatcher(graph)
    movie = matcher.match("Movie", id=int(id)).first()
    if not movie:
        return make_response(jsonify({"message": "Movie not found"}), 404)
    else:
        return make_response(jsonify(movie), 200)

# Delete Movie


@app.route('/api/admin/movies/<id>', methods=['DELETE'])
@jwt_required()
def delete(id):
    query = 'MATCH (m:Movie {id : $id}) DETACH DELETE m'
    # query = ('MATCH (mov:Movie) '
    #          ' WHERE mov.id = toInteger($id) '
    #          ' WITH mov '
    #          ' OPTIONAL MATCH (mov)-[r]-(allRelatedNodes) '
    #          ' WHERE size((allRelatedNodes)--()) = 1 '
    #          ' DETACH DELETE mov, allRelatedNodes ')
    try:
        graph.run(query, id=int(id))
        return make_response(jsonify({"message": "success"}), 200)
    except Exception as e:
        return (str(e))

# Add movie


@app.route('/api/admin/movies', methods=['POST', 'OPTIONS'])
@jwt_required()
def add_movie():
    if request.method == 'POST':
        id = uuid.uuid4().fields[1]
        title = request.form['title']
        poster = request.files['poster']
        content = request.form['content']
        duration = request.form['duration']
        language = request.form['language']
        country = request.form['country']
        genres = request.form['genres']
        year = request.form['year']
        actors = request.form['actors']
        url = request.form['url']
        slug = slugify(title)
        timestamp = calendar.timegm(time.gmtime())

        # filename = secure_filename(poster.filename)
        ext = poster.filename.split('.')[-1]
        filename = secure_filename(
            datetime.now().strftime("%Y_%m_%d_%I_%M_%S_%p") + "." + ext)
        poster.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        path = "static/Uploads" + '/' + filename

        movie = ' MERGE (u:Movie {id : $id,title: $title,poster: $poster,content: $content, duration: $duration, language: $language,year: $year,slug: $slug,timestamp: $timestamp, url: $url})'
        map = {"id": id, "title": title, "poster": path, "content": content, "duration": duration,
               "language": language, "year": year, "slug": slug, "timestamp": timestamp, "url": url}

        try:
            graph.run(movie, map)

            ctry = 'MERGE (c:Country {country: $country})'
            map = {"country": country}
            graph.run(ctry, map)

            relationship = 'MATCH (m:Movie) , (c:Country) WHERE m.slug = $slug and c.country = $country MERGE (m)-[r:PRODUCTED_BY]->(c) RETURN m,c'
            map = {"slug": slug, "country": country}
            graph.run(relationship, map)

            # format string before create
            genres = [x.strip() for x in genres.split(',')]
            genres = [genre.capitalize() for genre in genres]
            for gen in genres:
                id = id + 1
                gnr = 'MERGE (g:Genre {id: $id, name: $gen})'
                map = {"gen": gen, "id": id}
                graph.run(gnr, map)

                relationship = 'MATCH (m:Movie) , (g:Genre) WHERE m.slug = $slug and g.name = $gen MERGE (m)<-[r:IS_GENRE_OF]-(g) RETURN m,g'
                map = {"slug": slug, "gen": gen}
                print(map)
                graph.run(relationship, map)

            actors = [x.strip() for x in actors.split(',')]
            actors = [actor.title() for actor in actors]
            for actor in actors:
                print(actor)
                id = id + 1
                acts = 'MERGE (g:Actor {id: $id ,name: $actor})'
                map = {"actor": actor, "id":id}
                graph.run(acts, map)

                relationship = 'MATCH (m:Movie) , (a: Actor) WHERE m.slug = $slug and a.name = $actor MERGE (m)-[r:PARTICIPATION_OF]->(a) RETURN m,a'
                map = {"slug": slug, "actor": actor}
                print(map)
                graph.run(relationship, map)

            flash('add success')
            return make_response(jsonify({"message": "success"}), 200)
        except Exception as e:
            flash('Movie existed')
            print(e)
            return make_response(jsonify({"message": "Movie is Existed"}), 400)


# Update Movie
@app.route('/api/admin/movies/update/<id>', methods=['GET'])
@jwt_required()
def update_movie_get(id):
    query = 'MATCH (m:Movie) WHERE m.id = $id RETURN m as movie'
    movie = graph.run(query, id=int(id))
    check = movie.evaluate()

    if not check:
        return make_response(jsonify({"message": "Not Found"}), 404)

    return jsonify(check)

# Update Movie


@app.route('/api/admin/movies/update', methods=['PUT'])
@jwt_required()
def update_movie_put():
    id = request.form['id']
    title = request.form['title']
    poster = request.files['poster']
    content = request.form['content']
    duration = request.form['duration']
    language = request.form['language']
    year = request.form['year']
    url = request.form['url']
    slug = slugify(title)

    ext = poster.filename.split('.')[-1]
    filename = secure_filename(
        datetime.now().strftime("%Y_%m_%d_%I_%M_%S_%p") + "." + ext)
    poster.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    path = "static/Uploads" + '/' + filename

    query = ('MATCH (m:Movie {id : $id})'
             ' SET m.title = $title , m.poster = $poster, m.content = $content, m.duration = $duration, m.language = $language, m.year = $year, m.url = $url, m.slug = $slug'
             ' RETURN m.id')
    map = {"id": int(id), "title": title, "poster": path, "content": content,
           "duration": duration, "language": language, "slug": slug, "year": year, "url": url}
    try:
        graph.run(query, map)
        return make_response(jsonify({"message": "success"}), 200)
    except Exception as e:
        return (str(e))
    # else:
    #     query = ('MATCH (m:Movie {id : $id})'
    #              ' SET m.title = $title, m.content = $content, m.duration = $duration, m.language = $language, m.year = $year, m.url = $url ,m.slug = $slug'
    #              ' RETURN m.id')
    #     map = {"id": int(id), "title": title, "content": content,
    #            "duration": duration, "language": language, "slug": slug, "year": year, "url": url}
    #     try:
    #         graph.run(query, map)
    #         return make_response(jsonify({"message": "success"}), 200)
    #     except Exception as e:
    #         return (str(e))


# ================================================================


# Get all movies

@app.route('/api/movies', methods=['GET'])
def getAllMovieData():
    query = (
        'MATCH (c:Country)<-[:PRODUCTED_BY]-(m:Movie)<-[:IS_GENRE_OF]-(g:Genre) RETURN m AS movie, collect(g.name) AS genres, c.country AS country ORDER BY m.timestamp DESC')
    genre = graph.run(query)
    gen = genre.data()
    if gen:
        return make_response(jsonify(gen), 200)
    else:
        return make_response(jsonify({"message": "Opps! Something wrong"}), 404)


# Get the available details of a given movie


@app.route('/api/movies/<slug>', methods=['GET'])
@jwt_required()
def getMovieData(slug):
    query = (
        'MATCH (m:Movie {slug: $slug})<-[:IS_GENRE_OF]-(g:Genre) RETURN m AS movie, collect(g.name) AS genres')
    movie = graph.run(query, slug=slug).data()
    if not movie:
        return make_response(jsonify({"message": "Movie not found"}), 404)
    else:
        return make_response(jsonify(movie), 200)


# Get the submitted ratings of a given movie

@app.route('/api/movie/ratings/<title>')
def getMovieRatings(title):
    ratings = graph.run(
        'MATCH (u: User)-[r:RATED]->(m:Movie {title: $title}) RETURN u.id AS user, r.rating AS rating', title=title)

    return jsonify(ratings.data())


@app.route('/api/movie/average-rating/<title>')
def getMovieAverageRating(title):
    avg = graph.run(
        'MATCH (u: User)-[r:RATED]->(m:Movie {title: $title}) RETURN m.title AS title, avg(toFloat(r.rating)) AS '
        'averageRating', title=title)

    return jsonify(avg.data())


####### Top #######

# Get top N highest rated movies


@app.route('/api/top/movie/top-n/<n>')
def getMovieTopN(n):
    mvs = graph.run(
        'MATCH (u: User )-[r:RATED]->(m:Movie) RETURN m.title AS title, avg(r.rating) AS averageRating order by '
        'averageRating desc limit toInteger($n)', n=n)

    return jsonify(mvs.data())


# Get top N most rated movies


@app.route('/api/top/movie/n-most-rated/<n>')
def getMovieNMostRated(n):
    mvs = graph.run(
        'MATCH (u: User)-[r:RATED]->(m:Movie) RETURN m.title AS title, count(r.rating) as NumberOfRatings order by '
        'NumberOfRatings desc limit toInteger($n)', n=n)

    return jsonify(mvs.data())


# Recommender Engineer

# Content based


@app.route('/api/rec_engine/content', methods=['POST'])
@jwt_required()
def getRecContent():
    slug = request.json.get("slug", None)
    n = 20
    avg = graph.run('MATCH (m:Movie)<-[:IS_GENRE_OF]-(g:Genre)-[:IS_GENRE_OF]->(rec:Movie) '
                    'WHERE m.slug = $slug '
                    'WITH rec, COLLECT(g.name) AS genres, COUNT(*) AS numberOfSharedGenres '
                    'RETURN rec as movie, genres, numberOfSharedGenres '
                    'ORDER BY numberOfSharedGenres DESC LIMIT toInteger($n);', slug=slug, n=n)

    return jsonify(avg.data())


# Collaborative Filtering


@app.route('/api/rec_engine/collab', methods=['POST'])
@jwt_required()
def getRecCollab():
    username = request.json.get("username", None)
    n = 20
    rec = graph.run('MATCH (u1:User {username:$username})-[r:RATED]->(m:Movie) '
                    'WITH u1, avg(r.rating) AS u1_mean '
                    'MATCH (u1)-[r1:RATED]->(m:Movie)<-[r2:RATED]-(u2) '
                    'WITH u1, u1_mean, u2, COLLECT({r1: r1, r2: r2}) AS ratings WHERE size(ratings) > 3 '
                    'MATCH (u2)-[r:RATED]->(m:Movie) '
                    'WITH u1, u1_mean, u2, avg(r.rating) AS u2_mean, ratings '
                    'UNWIND ratings AS r '
                    'WITH sum( (r.r1.rating-u1_mean) * (r.r2.rating-u2_mean) ) AS nom, '
                    'sqrt( sum( (r.r1.rating - u1_mean)^2) * sum( (r.r2.rating - u2_mean) ^2)) AS denom, u1, '
                    'u2 WHERE denom <> 0 '
                    'WITH u1, u2, nom/denom AS pearson '
                    'ORDER BY pearson DESC LIMIT 10 '
                    
                    'MATCH (u2)-[r:RATED]->(m:Movie)<-[:IS_GENRE_OF]-(g:Genre) WHERE NOT EXISTS( (u1)-[:RATED]->(m) ) '
                    'RETURN collect(g.name) AS genres, m AS movie, SUM( pearson * r.rating) AS score '
                    'ORDER BY score DESC LIMIT toInteger($n);', username=username, n=n)

    return jsonify(rec.data())

# Create
UPLOAD_FOLDER = 'api/static/Uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Show All Movie
@app.route('/api/movie/all_movie', methods=['GET'])
def show_all_movie():
    query = 'MATCH (m:Movie) RETURN m ORDER BY m.timestamp DESC'
    movie = graph.run(query)
    mov = movie.data()
    if mov:
        return jsonify(mov)
    else:
        return make_response(jsonify({"message": "None"}), 200)


# Get rating

# MATCH (u:User)-[r:RATED]->(m:Movie {title: "Toy Story 2"})RETURN avg(r.rating) AS rating


@app.route('/api/rating/<slug>', methods=['GET'])
@jwt_required()
def get_rating_movie(slug):
    try:
        query = (
            "MATCH (u:User)-[r:RATED]->(m:Movie {slug: $slug}) RETURN avg(r.rating)")
        result = graph.run(query, slug=slug).evaluate()
        return make_response(jsonify({"rating": result}), 200)
    except Exception as e:
        print(str(e))
        return (str(e))


# Rating movie

@app.route('/api/rating', methods=['POST'])
@jwt_required()
def rating_movie():
    movie_slug = request.json.get("movie_slug", None)
    username = request.json.get('username', None)
    rating = request.json.get('rating', None)
    timestamp = calendar.timegm(time.gmtime())
    try:
        query = ('MATCH (m:Movie{slug:$slug}),(u:User{username:$username})'
                 'MERGE (u)-[r:RATED]->(m) '
                 'ON CREATE SET r.rating =  $rating, r.timestamp = $timestamp '
                 'ON MATCH SET r.rating =$rating , r.timestamp = $timestamp '
                 ' RETURN m')
        graph.run(query, username=username, timestamp=timestamp,
                  rating=rating, slug=movie_slug)
        return make_response(jsonify({"message": "success"}), 200)
    except Exception as e:
        print(str(e))
        return (str(e))

# MATCH (p:Movie)
# WHERE p.title =~ 'T.*'
# RETURN p.title
@app.route('/api/movies/search', methods=['GET'])
def search_movie():
    movie_title = request.args.get('query')
    movie_title+=".*"
    query = (
        'MATCH (m:Movie)<-[:IS_GENRE_OF]-(g:Genre) WHERE m.title =~ $movie_title RETURN m AS movie, collect(g.name) AS genres')
    genre = graph.run(query, movie_title=movie_title.capitalize())
    gen = genre.data()
    if gen:
        return make_response(jsonify(gen), 200)
    else:
        return make_response(jsonify({"message": "Opps! Something wrong"}), 404)