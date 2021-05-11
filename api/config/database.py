from py2neo import Graph


class Database:
    PATH = "bolt://localhost:7687"
    USERNAME = "neo4j"
    PASS = "123456"

    def __init__(self):
        self.path = Database.PATH
        self.username = Database.USERNAME
        self.password = Database.PASS

    def connect(self):
        graph = Graph(self.path, auth=(self.username, self.password))
        return graph
