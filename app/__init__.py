import logging
import os
import signal

import click
#from psycopg2cffi import compat
#compat.register()
from alembic import command
from flask import Flask, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_httpauth import HTTPTokenAuth
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_sso import SSO
from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists, drop_database

from app.elastic_index import ElasticIndex
from app.email_service import EmailService
from app.file_server import FileServer
from app.rest_exception import RestException

app = Flask(__name__, instance_relative_config=True)
""":type: flask.app.Flask"""

# Load the configuration from the instance folder
app.config.from_pyfile('settings.py')
# Load the file specified by the APP_CONFIG_FILE environment variable
# Variables defined here will override those in the default configuration
if "APP_CONFIG_FILE" in os.environ:
    app.config.from_envvar('APP_CONFIG_FILE')

if(app.config['DEBUG']):
    app.debug = True

# Enable CORS
if(app.config['CORS_ENABLED']):
    cors = CORS(app, resources={r"*": {"origins": "*"}})

# Database Configuration
logging.basicConfig()
logger = logging.getLogger('sqlalchemy.engine')
logger.setLevel(app.config['SQLALCHEMY_LOG_LEVEL'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
""":type: sqlalchemy.orm.SQLAlchemy"""

# Flask-Marshmallow provides HATEOAS links
ma = Marshmallow(app)
""":type: flask_marshmallow.Marshmallow"""

# Database Migrations
migrate = Migrate(app, db)

# Search System
elastic_index = ElasticIndex(app)

# file Server
file_server = FileServer(app)

# email service
email_service = EmailService(app)

# Single Signon
sso = SSO(app=app)

# Token Authentication
auth = HTTPTokenAuth('Bearer')

# Password Encryption
bcrypt = Bcrypt(app)


@app.cli.command()
def stop():
    """Stop the server."""
    pid = os.getpid()
    if pid:
        print('Stopping server...')
        os.kill(pid, signal.SIGTERM)
        print('Server stopped.')
    else:
        print('Server is not running.')

# Constructing for a problem when building urls when the id is null.
# there is a fix in the works for this, see
# https://github.com/kids-first/kf-api-dathanaservice/pull/219
# handler = lambda error, endpoint, values: ''


def handler(error, endpoint, values=''):
    print('URL Build error:' + str(error))
    return ''


app.url_build_error_handlers.append(handler)

# Handle errors consistently
@app.errorhandler(RestException)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(404)
def handle_404(error):
    return handle_invalid_usage(RestException(RestException.NOT_FOUND, 404))


def _load_data(data_loader):
    data_loader.load_institutions()
    data_loader.load_resources()
    data_loader.load_availability()
    # data_loader.load_icons()
    data_loader.load_categories()
    data_loader.load_resource_categories()
    data_loader.load_users()
    data_loader.load_user_favorites()


def _loadicons():
    """Load the SVG icon images onto the S3 bucket and create records in the database"""
    click.echo('Loading SVG Images to S3, creating Icon Records')
    from app import data_loader
    data_loader = data_loader.DataLoader()
    data_loader.load_icons()


def _loaddb():
    """Initialize the database."""
    from app import data_loader
    data_loader = data_loader.DataLoader()
    _load_data(data_loader)


def _loadindex():
    """Load all information into the elastic search Index."""
    click.echo('Loading data into Elastic Search')
    from app import data_loader
    data_loader = data_loader.DataLoader()
    data_loader.build_index()


def _clearindex():
    """Delete all information from the elasticsearch index"""
    click.echo('Removing Data from Elastic Search')
    from app import data_loader
    data_loader = data_loader.DataLoader()
    data_loader.clear_index()


def _setup():
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    if not database_exists(engine.url):
        try:
            create_database(engine.url)
            click.echo('Database created..........')
            if app.config['ALEMBIC_PRINT_SQL']:
                command.upgrade(migrate.get_config(), 'head', True)
            command.upgrade(migrate.get_config(), 'head')
            click.echo('Database revision changes applied..........')
            _loadicons()
            click.echo(
                'Database SVG icon images loaded into the S3 bucket and respective records initialized in the database..........')
            _loaddb()
            click.echo('Database initialized with data..........')
            _loadindex()
            click.echo('Elastic search database initalized with data..........')
        except Exception as ex:
            click.echo('Failed to setup. Please DEBUG and try again')
            raise ex
    else:
        click.echo('Cannot setup: Database already exists')
        if app.config['ALEMBIC_PRINT_SQL']:
            command.upgrade(migrate.get_config(), 'head', True)
        command.upgrade(migrate.get_config(), 'head')
        click.echo('Database revision changes applied..........')
        _loadindex()
        click.echo('Elastic search database initalized with data..........')


def _teardown():
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    if database_exists(engine.url):
        try:
            drop_database(engine.url)
            click.echo('Database dropped..........')
            _clearindex()
            click.echo('Elastic search database indexes cleared..........')
        except Exception as ex:
            click.echo('Failed to teardown. Please DEBUG and try again')
            raise ex
    else:
        click.echo('Cannot teardown: Database does not exist')


@app.cli.command()
def setupapp():
    _setup()
    click.echo('Setup completed...............')


@app.cli.command()
def teardownapp():
    _teardown()
    click.echo('Teardwon completed...............')


@app.cli.command()
def resetapp():
    _teardown()
    _setup()


@app.cli.command()
def loadicons():
    _loadicons()


@app.cli.command()
def initdb():
    _loaddb()


@app.cli.command()
def initindex():
    _loadindex()


@app.cli.command()
def cleardb():
    """Delete all information from the database."""
    click.echo('Clearing out the database')
    from app import data_loader
    data_loader = data_loader.DataLoader()
    data_loader.clear()


@app.cli.command()
def clearindex():
    _clearindex()


@app.cli.command()
def reset():
    """Remove all data and recreate it from the example data files"""
    click.echo('Rebuilding the databases from the example data files')
    from app import data_loader
    data_loader = data_loader.DataLoader()
    data_loader.clear_index()
    data_loader.clear()
    _load_data(data_loader)
    data_loader.build_index()

from app import views
