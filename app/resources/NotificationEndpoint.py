import flask_restful
from flask import g, request

from app import auth, RestException
from app.models import NotificationStatus
from app.resources.schema import NotificationSchema
from app.services.notifications_service import NotificationsService

"""Provides a way to get the current user's notifications and take action on them."""


class NotificationListEndpoint(flask_restful.Resource):
    # Get list of notifications for the current user
    @auth.login_required
    def get(self):
        if 'user' not in g:
            raise RestException(RestException.PERMISSION_DENIED)

        notifications = NotificationsService.get_notifications_for_user(g.user.id)

        if notifications is not None:
            return NotificationSchema(many=True).dump(notifications)
        else:
            raise RestException(RestException.NOT_FOUND)


class NotificationEndpoint(flask_restful.Resource):
    # Gets a single notification by id
    @auth.login_required
    def get(self, notification_id):
        if 'user' not in g:
            raise RestException(RestException.PERMISSION_DENIED)

        notification = NotificationsService.get_notification(g.user.id, notification_id)

        if notification is not None:
            return NotificationSchema().dump(notification)
        else:
            raise RestException(RestException.NOT_FOUND)

    # Updates status of a single notification
    @auth.login_required
    def post(self, notification_id):
        if 'user' not in g:
            raise RestException(RestException.PERMISSION_DENIED)

        request_data = request.get_json()
        if 'status' in request_data:
            status_str = request_data['status']
            updated_notification = NotificationsService.update_notification_status(
                g.user.id,
                notification_id,
                NotificationStatus[status_str]
            )

            return NotificationSchema().dump(updated_notification)
        else:
            raise RestException(RestException.INVALID_OBJECT)


class NotificationActionEndpoint(flask_restful.Resource):
    # Take action on a notification
    @auth.login_required
    def post(self, notification_id, action_id):
        if 'user' not in g:
            raise RestException(RestException.PERMISSION_DENIED)

        # Check that the notification requested was actually sent to the user
        db_notification = NotificationsService.get_notification(g.user.id, notification_id)

        if db_notification is None:
            raise RestException(RestException.NOT_FOUND)

        # Get the notification action that was sent
        db_action_sent = NotificationsService.get_notification_action_sent(g.user.id, notification_id, action_id)

        # If the action was actually sent to the user, record the action as taken.
        if db_action_sent is None:
            raise RestException(RestException.NOT_FOUND)

        updated_notification = NotificationsService.take_notification_action(g.user.id, notification_id, action_id)
        return NotificationSchema().dump(updated_notification)
