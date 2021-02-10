from config.base import *

CORS_ENABLED = True

ALEMBIC_PRINT_SQL = True
DEBUG = True

# SQLALCHEMY/ALEMBIC Settings

# Amazon S3 Bucket for storing images.

# Elastic Search Settings

# SMTP Email Settings

# Single Signon configuration Settings
SSO_ATTRIBUTE_MAP['uid'] = (False, 'uid')
SSO_DEVELOPMENT_EPPN = 'ajl2j@virginia.edu'
MAIL_CONSULT_RECIPIENT = 'ajl2j@virginia.edu'

API_URL = 'http://localhost:5000'
SITE_URL = 'http://localhost:4200'
FRONTEND_AUTH_CALLBACK, FRONTEND_EMAIL_RESET, FRONTEND_EMAIL_CONFIRM = auth_callback_url_tuple(
    SITE_URL, '/#/session', '/#/reset_password/', '/#/login/')
API_UVARC_URL = 'http://localhost:5001/rest/v2/'
