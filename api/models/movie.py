
from py2neo import Node
from api.config.database import Database
graph = Database().connect()

# class Movie:
#     def __init__(self):
#         self.slug = slug
#
#     def find_movie_by_slug(self):
#         movie = graph.nodes.match("Movie",slug = self.slug).first()
#         return movie
    


