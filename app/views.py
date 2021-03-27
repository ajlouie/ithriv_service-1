from flask import jsonify, url_for, redirect, g, request, Blueprint
from app import app, db, sso, auth, RestException
import flask_restful
from flask_restful import reqparse
import urllib

from app.resources.Auth import auth_blueprint
from app.resources.FileEndpoint import FileListEndpoint, FileEndpoint
from app.resources.IconEndpoint import IconListEndpoint, IconEndpoint
from app.resources.ResourceAndCategoryEndoint import ResourceByCategoryEndpoint, CategoryByResourceEndpoint, \
    ResourceCategoryEndpoint, ResourceCategoryListEndpoint
from app.resources.ResourceEndpoint import ResourceListEndpoint, ResourceEndpoint, UserResourceEndpoint
from app.resources.CategoryEndoint import CategoryListEndpoint, CategoryEndpoint, RootCategoryListEndpoint
from app.resources.AvailabilityEndpoint import AvailabilityEndpoint, AvailabilityListEndpoint, \
    ResourceAvailabilityEndpoint
from app.resources.InstitutionEndpoint import InstitutionEndpoint, InstitutionListEndpoint, \
    InstitutionAvailabilityListEndpoint
from app.resources.SearchEndpoint import SearchEndpoint
from app.resources.SessionEndpoint import SessionEndpoint
from app.resources.SessionStatusEndpoint import SessionStatusEndpoint
from app.resources.Tracking import tracking_blueprint
from app.resources.ApprovalRequest import approval_blueprint
from app.resources.ConsultRequest import consult_blueprint
from app.resources.TypeEndpoint import TypeEndpoint, TypeListEndpoint, SegmentListEndpoint
from app.resources.UserEndpoint import UserEndpoint, UserListEndpoint
from app.resources.FavoriteEndpoint import UserFavoriteEndpoint, FavoriteEndpoint, FavoriteListEndpoint
from app.resources.NotificationEndpoint import NotificationEndpoint, NotificationActionEndpoint, \
    NotificationListEndpoint, NotificationActionListEndpoint, NotificationActionAdminEndpoint, NotificationSendEndpoint


class IThrivApi(flask_restful.Api):
    # Define a custom error handler for all rest endpoints that
    # properly handles the RestException status.
    def handle_error(self, e):
        response = jsonify(e.to_dict())
        response.status_code = e.status_code
        flask_restful.abort(e.status_code, response)


api_blueprint = Blueprint("api", __name__, url_prefix='/api')
api = IThrivApi(api_blueprint)
app.register_blueprint(api_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(tracking_blueprint)
app.register_blueprint(consult_blueprint)
app.register_blueprint(approval_blueprint)

parser = flask_restful.reqparse.RequestParser()
parser.add_argument('resource')

endpoints = [
    (ResourceListEndpoint, '/resource'),
    (ResourceEndpoint, '/resource/<id>'),
    (CategoryByResourceEndpoint, '/resource/<resource_id>/category'),
    (CategoryListEndpoint, '/category'),
    (CategoryEndpoint, '/category/<id>'),
    (RootCategoryListEndpoint, '/category/root'),
    (ResourceByCategoryEndpoint, '/category/<category_id>/resource'),
    (InstitutionEndpoint, '/institution/<id>'),
    (InstitutionListEndpoint, '/institution'),
    (InstitutionAvailabilityListEndpoint, '/institution/availability'),
    (TypeEndpoint, '/type/<id>'),
    (TypeListEndpoint, '/type'),
    (SearchEndpoint, '/search'),
    (SegmentListEndpoint, '/segment'),
    (ResourceCategoryListEndpoint, '/resource_category'),
    (ResourceCategoryEndpoint, '/resource_category/<id>'),
    (AvailabilityListEndpoint, '/availability'),
    (AvailabilityEndpoint, '/availability/<id>'),
    (ResourceAvailabilityEndpoint, '/resource/<resource_id>/availability'),
    (IconListEndpoint, '/icon'),
    (IconEndpoint, '/icon/<id>'),
    (UserListEndpoint, '/user'),
    (UserEndpoint, '/user/<id>'),
    (SessionEndpoint, '/session'),
    (SessionStatusEndpoint, '/session_status'),
    (FavoriteListEndpoint, '/favorite'),
    (FavoriteEndpoint, '/favorite/<id>'),
    (UserFavoriteEndpoint, '/session/favorite'),
    (UserResourceEndpoint, '/session/resource'),
    (FileEndpoint, '/file/<id>'),
    (FileListEndpoint, '/file'),
    (NotificationListEndpoint, '/notification'),
    (NotificationEndpoint, '/notification/<notification_id>'),
    (NotificationActionEndpoint, '/notification/<notification_id>/action/<action_id>'),
    (NotificationActionListEndpoint, '/notification_action'),
    (NotificationActionAdminEndpoint, '/notification_action/<action_id>'),
    (NotificationSendEndpoint, '/notification_send'),
]


@app.route('/', methods=['GET'])
def root():
    output = {}
    for rule in app.url_map.iter_rules():
        options = {}
        for arg in rule.arguments:
            options[arg] = "<{0}>".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        output[rule.endpoint] = urllib.parse.unquote(url)

    return jsonify(output)


for endpoint in endpoints:
    api.add_resource(endpoint[0], endpoint[1])
