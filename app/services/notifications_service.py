from sqlalchemy import desc

from app import session, RestException
from app.models import Notification, NotificationActionSent, NotificationAction, NotificationActionTaken, \
    NotificationStatus
from app.resources.schema import NotificationActionSchema


class NotificationsService(object):

    @staticmethod
    def is_valid_notification(user_id, notification_id):
        db_notification = NotificationsService.get_notification(user_id, notification_id)
        return db_notification is not None and db_notification.id is not None

    @staticmethod
    def is_valid_action(action_id):
        num_actions = session.query(NotificationAction).filter(NotificationAction.id == action_id).count()
        return num_actions > 0

    @staticmethod
    def is_valid_status(status_str):
        return status_str in set(item.value for item in NotificationStatus)

    @staticmethod
    def was_action_sent(user_id, notification_id, action_id):
        db_action_sent = NotificationsService.get_notification_action_sent(user_id, notification_id, action_id)
        return db_action_sent is not None and db_action_sent.id is not None

    @staticmethod
    def get_notifications_for_user(user_id):
        return session.query(Notification) \
            .filter(Notification.user_id == user_id) \
            .order_by(desc(Notification.last_updated)) \
            .all()

    @staticmethod
    def get_notification(user_id, notification_id):
        return session.query(Notification) \
            .filter(Notification.user_id == user_id) \
            .filter(Notification.id == notification_id) \
            .first()

    @staticmethod
    def get_action(action_id):
        if NotificationsService.is_valid_action(action_id):
            return session.query(NotificationAction).filter(NotificationAction.id == action_id).first()

    @staticmethod
    def get_notification_actions(user):
        if user.role != 'Admin':
            raise RestException(RestException.PERMISSION_DENIED)

        return session.query(NotificationAction) \
            .order_by(desc(NotificationAction.title)) \
            .all()

    @staticmethod
    def add_notification_action(user, action_dict):
        if user.role != 'Admin':
            raise RestException(RestException.PERMISSION_DENIED)

        new_action, errors = NotificationActionSchema().load(data=action_dict)
        if errors:
            raise RestException(RestException.INVALID_OBJECT, details=errors)
        session.add(new_action)
        session.commit()

        # Return new action by criteria, since we can't guarantee it'll have an ID right away.
        return session.query(NotificationAction) \
            .filter(NotificationAction.title == new_action.title) \
            .filter(NotificationAction.description == new_action.description) \
            .filter(NotificationAction.type == new_action.type) \
            .filter(NotificationAction.url == new_action.url) \
            .order_by(desc(NotificationAction.date_created)) \
            .first()

    @staticmethod
    def update_notification_action(user, action_id, action_dict):
        if user.role != 'Admin':
            raise RestException(RestException.PERMISSION_DENIED)

        if NotificationsService.is_valid_action(action_id):
            instance = session.query(NotificationAction).filter(NotificationAction.id == action_id).first()
            updated_action, errors = NotificationActionSchema().load(data=action_dict, instance=instance)
            if errors:
                raise RestException(RestException.INVALID_OBJECT, details=errors)
            session.add(updated_action)
            session.commit()

            # Return updated action
            return NotificationsService.get_action(action_id)
        else:
            NotificationsService.raise_invalid_action(action_id=action_id)

    @staticmethod
    def delete_notification_action(user, action_id):
        if user.role != 'Admin':
            raise RestException(RestException.PERMISSION_DENIED)

        if NotificationsService.is_valid_action(action_id):
            session.query(NotificationAction) \
                .filter(NotificationAction.id == action_id) \
                .delete()

            session.commit()
        else:
            NotificationsService.raise_invalid_action(action_id=action_id)

    @staticmethod
    def get_notification_action_sent(user_id, notification_id, action_id):
        # Check that the notification is valid
        if not NotificationsService.is_valid_notification(user_id, notification_id):
            NotificationsService.raise_invalid_notification_params(user_id, notification_id)

        # Check that the action is valid
        if not NotificationsService.is_valid_action(action_id):
            NotificationsService.raise_invalid_action(notification_id, action_id)

        return session.query(NotificationActionSent) \
            .filter(NotificationActionSent.notification_id == notification_id) \
            .filter(NotificationActionSent.notification_action_id == action_id) \
            .first()

    @staticmethod
    def add_notification_for_user(user_id, title, description, expiration_date=None, action_ids=[]):
        if len(action_ids) == 0:
            raise RestException({
                'code': 'invalid_notification_params',
                'message': 'You must provide a list of valid action IDs for the new notification.'
            })

        new_notification = Notification(
            user_id=user_id,
            title=title,
            description=description,
            expiration_date=expiration_date
        )
        session.add(new_notification)
        session.commit()

        # Get the new notification from the database, so we can get its ID.
        db_notification = session.query(Notification) \
            .filter(Notification.user_id == user_id) \
            .filter(Notification.title == title) \
            .filter(Notification.description == description) \
            .order_by(desc(Notification.date_created)) \
            .first()

        # Add actions for the new notification.
        if db_notification is not None and db_notification.id is not None:
            for action_id in action_ids:
                # Verify that the action ID is valid.
                if not NotificationsService.is_valid_action(action_id):
                    NotificationsService.raise_invalid_action(db_notification.id, action_id)

                new_action_sent = NotificationActionSent(
                    notification_id=db_notification.id,
                    notification_action_id=action_id
                )
                session.add(new_action_sent)
            session.commit()
        else:
            raise RestException({'code': 'invalid_notification', 'message': 'Cannot retrieve new notification.'})

        # Return the new notification
        return NotificationsService.get_notification(user_id, db_notification.id)

    @staticmethod
    def update_notification_status(user_id, notification_id, status_str):
        if not NotificationsService.is_valid_status(status_str):
            NotificationsService.raise_invalid_status(status_str)

        if NotificationsService.is_valid_notification(user_id, notification_id):
            session.query(Notification) \
                .filter(Notification.user_id == user_id) \
                .filter(Notification.id == notification_id) \
                .update({'status': NotificationStatus[status_str]})

            session.commit()
            return NotificationsService.get_notification(user_id, notification_id)
        else:
            NotificationsService.raise_invalid_notification_params(user_id, notification_id)

    @staticmethod
    def take_notification_action(user_id, notification_id, action_id):
        # Make sure the notification is valid and that this is a valid action to take
        if NotificationsService.was_action_sent(user_id, notification_id, action_id):
            action_taken = NotificationActionTaken(notification_id=notification_id, notification_action_id=action_id)
            session.add(action_taken)
            session.commit()

            NotificationsService.update_notification_status(user_id, notification_id, NotificationStatus.action_taken)

            # Return the updated notification
            return NotificationsService.get_notification(user_id, notification_id)
        else:
            NotificationsService.raise_invalid_action(notification_id, action_id)

    @staticmethod
    def raise_invalid_notification_params(user_id, notification_id):
        raise RestException({
            'code': 'invalid_notification_params',
            'message': f'Cannot retrieve the notification. Either the user_id ({user_id}) '
                       f'or notification_id ({notification_id}) are invalid.'
        })

    @staticmethod
    def raise_invalid_action(notification_id=None, action_id=None):
        if notification_id is not None:
            raise RestException({
                'code': 'invalid_notification_action',
                'message': f'The action_id {action_id} is not valid for notification_id {notification_id}.'
            })
        else:
            raise RestException({
                'code': 'invalid_notification_action',
                'message': f'The action_id {action_id} is not valid.'
            })

    @staticmethod
    def raise_invalid_status(status_str):
        raise RestException({
            'code': 'invalid_notification_status',
            'message': f'The notification status name "{status_str}" is not a valid NotificationStatus.'
        })
