import flask_restful
from flask import g

from app import db, auth, RestException
from app.models import Notification, NotificationActionSent, NotificationActionTaken
from app.resources.schema import NotificationSchema

"""Provides a way to get the current user's notifications and take action on them."""


class NotificationListEndpoint(flask_restful.Resource):
    # Get list of notifications for the current user
    @auth.login_required
    def get(self):
        if 'user' not in g:
            raise RestException(RestException.PERMISSION_DENIED)

        notifications = db.session.query(Notification) \
            .filter(Notification.user_id == g.user.id) \
            .order_by(Notification.last_updated.desc()) \
            .all()

        if notifications is not None:
            return NotificationSchema(many=True).dump(notifications)
        else:
            raise RestException(RestException.NOT_FOUND)


class NotificationEndpoint(flask_restful.Resource):
    # Get a single notification
    @auth.login_required
    def get(self, notification_id):
        notification = db.session.query(Notification) \
            .filter(Notification.user_id == g.user.id) \
            .filter(Notification.id == notification_id) \
            .first()

        if notification is not None:
            return NotificationSchema().dump(notification)
        else:
            raise RestException(RestException.NOT_FOUND)


class NotificationActionEndpoint(flask_restful.Resource):
    # Take action on a notification
    @auth.login_required
    def post(self, notification_id, action_id):
        # Check that the notification requested was actually sent to the user
        db_notification = db.session.query(Notification)\
            .filter(Notification.user_id == g.user.id)\
            .filter(Notification.id == notification_id)\
            .first()

        if db_notification is None:
            raise RestException(RestException.NOT_FOUND)

        # Get the notification action that was sent
        db_action_sent = db.session.query(NotificationActionSent) \
            .filter(NotificationActionSent.notification_id == notification_id) \
            .filter(NotificationActionSent.notification_action_id == action_id) \
            .first()

        # If the action was actually sent to the user, record the action as taken.
        if db_action_sent is not None:
            action_taken = NotificationActionTaken(
                notification_id=notification_id,
                notification_action_id=action_id
            )

            db.session.add(action_taken)
            db.session.commit()
        else:
            raise RestException(RestException.NOT_FOUND)
