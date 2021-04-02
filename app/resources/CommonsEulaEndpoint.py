import datetime

import flask_restful
from flask import request

from app import RestException, auth, session
from app.resources.schema import UserSchema
from app.services.user_service import UserService
from app.models import User


class CommonsEulaEndpoint(flask_restful.Resource):

    @auth.login_required
    def post(self):
        request_data = request.get_json()

        if not ('user_id' in request_data or 'user_accepted' in request_data):
            raise RestException(RestException.INVALID_OBJECT)

        try:
            user_id = request_data['user_id']
            user_accepted = request_data['user_accepted']

            if UserService.is_valid_user(user_id):
                session.query(User) \
                    .filter(User.id == user_id) \
                    .update({
                        'commons_eula_accepted': user_accepted,
                        'commons_eula_accepted_date': datetime.datetime.now() if user_accepted else None
                    })

                session.commit()
                updated_user = UserService.get_user(user_id)
                return UserSchema().dump(updated_user)

        except Exception as err:
            raise RestException(RestException.INVALID_OBJECT, details=err)
