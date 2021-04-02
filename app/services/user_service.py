from app import session, RestException
from app.models import User


class UserService(object):

    @staticmethod
    def is_valid_user(user_id):
        if user_id is None:
            return False

        db_user = session.query(User) \
            .filter(User.id == user_id) \
            .first()

        return db_user is not None

    @staticmethod
    def get_user(user_id):
        if UserService.is_valid_user(user_id):
            return session.query(User) \
                .filter(User.id == user_id) \
                .first()
        else:
            raise RestException(RestException.NOT_FOUND)


