from config.base import *

CORS_ENABLED = True

ALEMBIC_PRINT_SQL = True
DEBUG = True
TESTING = True

# SQLALCHEMY/ALEMBIC Settings
SQLALCHEMY_DATABASE_URI = "postgresql://ed_user:ed_pass@localhost/ithriv_test"

# Amazon S3 Bucket for storing images.

# Elastic Search Settings
ELASTIC_SEARCH = {
    "index_prefix": "ithriv_test",
    "hosts": ["localhost"],
    "port": 9200,
    "timeout": 20,
    "verify_certs": False,
    "use_ssl": False,
    "http_auth_user": "",
    "http_auth_pass": ""
}

# SMTP Email Settings

# Single Signon configuration Settings
SSO_ATTRIBUTE_MAP['uid'] = (False, 'uid')
SSO_DEVELOPMENT_EPPN = 'ithriv_admin@virginia.edu'
MAIL_CONSULT_RECIPIENT = 'rkc7h@virginia.edu'

API_URL = 'http://localhost:5000'
SITE_URL = 'http://localhost:4200'
FRONTEND_AUTH_CALLBACK, FRONTEND_EMAIL_RESET, FRONTEND_EMAIL_CONFIRM = auth_callback_url_tuple(
    SITE_URL, '/#/session', '/#/reset_password/', '/#/login/')
API_UVARC_URL = 'http://localhost:5001/rest/v2/'
