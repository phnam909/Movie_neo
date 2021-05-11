from api import app

PORT = 9000
HOST = '127.0.0.1'

if __name__ == "__main__":
    app.run(port=PORT, host=HOST, debug=True)
