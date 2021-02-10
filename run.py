from app import app
from os import getenv

if __name__ == '__main__':
    port = getenv('FLASK_RUN_PORT', default=5000)
    app.run(threaded=True, port=port)
