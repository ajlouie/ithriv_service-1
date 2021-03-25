import datetime
import enum
import re

import jwt
from flask import g
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

from app import RestException, app, bcrypt, db

Base = declarative_base()


class Category(db.Model):
    ''' Top Level Categories should have an image and color.  Second level categories should
        contain an icon.  Not inforcing this presently, but that is the general style.  '''
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    # Shorter description of the category
    brief_description = db.Column(db.String)
    description = db.Column(db.String)  # Complete description of the category
    parent_id = db.Column(db.Integer, db.ForeignKey(
        'category.id'), nullable=True)
    color = db.Column(db.String)  # Should be a CSS color specification
    # Should be the url for a large background image
    image = db.Column(db.String)
    display_order = db.Column(db.Integer, default=999)
    children = db.relationship("Category",
                               backref=db.backref('parent', remote_side=[id]),
                               lazy="joined",
                               join_depth=2,
                               order_by="Category.display_order, Category.name")
    icon_id = db.Column(db.Integer, db.ForeignKey('icon.id'))
    icon = db.relationship("Icon")

    def calculate_color(self):
        """Color is inherited from the parent category if not set explicitly."""
        color = self.color
        cat = self.parent
        while not self.color and cat:
            color = cat.color
            cat = cat.parent
        return color

    def calculate_level(self):
        """Provide the depth of the category """
        level = 0
        cat = self
        while cat.parent:
            level = level + 1
            cat = cat.parent
        return level


class EmailLog(db.Model):
    __tablename__ = 'email_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('ithriv_user.id'))
    type = db.Column(db.String)
    tracking_code = db.Column(db.String)
    viewed = db.Column(db.Boolean)
    date_viewed = db.Column(db.DateTime)


class Favorite(db.Model):
    __tablename__ = 'favorite'
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(
        'resource_id',
        db.Integer,
        db.ForeignKey('resource.id'),
        nullable=False)
    user_id = db.Column(
        'user_id', db.Integer, db.ForeignKey('ithriv_user.id'), nullable=False)


class Icon(db.Model):
    __tablename__ = 'icon'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    url = db.Column(db.String)


class ThrivInstitution(db.Model):
    __tablename__ = 'institution'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    domain = db.Column(db.String)
    resources = db.relationship(
        'ThrivResource', backref=db.backref('institution', lazy=True))
    hide_availability = db.Column(db.Boolean, default=False)


class Availability(db.Model):
    __tablename__ = 'availability'
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column('resource_id', db.Integer,
                            db.ForeignKey('resource.id'))
    institution_id = db.Column('institution_id', db.Integer,
                               db.ForeignKey('institution.id'))
    institution = db.relationship(ThrivInstitution)
    available = db.Column(db.Boolean)


class ThrivResource(db.Model):
    '''A resource is meta data about a website, database, group, institution
       or other entity that might prove useful to medical research, clinical
       application, or to educate and empower the community'''
    __tablename__ = 'resource'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    last_updated = db.Column(db.DateTime, default=datetime.datetime.now)
    description = db.Column(db.String)
    owner = db.Column(db.String)
    contact_email = db.Column(db.String)
    contact_phone = db.Column(db.String)
    contact_notes = db.Column(db.String)
    website = db.Column(db.String)
    cost = db.Column(db.String)
    type_id = db.Column('type_id', db.Integer, db.ForeignKey('type.id'))
    institution_id = db.Column('institution_id', db.Integer,
                               db.ForeignKey('institution.id'))
    availabilities = db.relationship(
        lambda: Availability,
        cascade="all, delete-orphan",
        backref=db.backref('resource', lazy=True))
    favorites = db.relationship(
        lambda: Favorite,
        cascade="all, delete-orphan",
        backref=db.backref('resource', lazy=True))
    files = db.relationship("UploadedFile", back_populates="resource")
    categories = db.relationship("ResourceCategory", back_populates="resource")
    approved = db.Column(db.String)
    private = db.Column(db.Boolean, default=False)
    segment_id = db.Column('segment_id', db.Integer,
                           db.ForeignKey('segment.id'), nullable=False)
    location = db.Column(db.String)
    starts = db.Column(db.DateTime)
    ends = db.Column(db.DateTime)

    def favorite_count(self):
        return len(self.favorites)

    def owners(self):
        try:
            return re.split('; |, | ', self.owner)
        except Exception:
            return []

    def user_may_view(self):
        try:
            if('user' in g and g.user is not None):
                if(g.user.email in self.owners()):
                    return True
                elif ((self.private is None or self.private is False)
                        or self.institution.description == g.user.institution.description):
                    if (self.approved == 'Approved'):
                        return True
                    elif (g.user.role == "Admin"):
                        return True
            elif ((self.private is None or self.private is False)
                  and self.approved == 'Approved'):
                return True
            return False

            # # if resource is private,
            # # user institution must match resource institution
            # if 'user' in g and g.user:
            #     owners = self.owners()
            #     if owners and g.user.email in owners:
            #         return True
            #     elif g.user.role == "Admin":
            #         if self.private:
            #             return self.institution_id == g.user.institution_id
            #         else:
            #             return True
            #     elif g.user.role == "User":
            #         if self.private:
            #             return (self.approved == "Approved") and (self.institution_id == g.user.institution_id)
            #         else:
            #             return (self.approved == "Approved")
            #     else:
            #         return False
            # else:
            #     if self.private:
            #         return (self.approved == "Approved") and (not self.private)
            #     else:
            #         return (self.approved == "Approved")

        except Exception:
            return False

    def user_may_edit(self):
        try:
            if not hasattr(g, 'user') or not g.user:
                return False
            elif self.owners() and g.user.email in self.owners():
                return True
            elif g.user.role == "Admin":
                if self.private:
                    return (self.institution_id == g.user.institution_id)
                else:
                    return True
            else:
                return False
        except Exception:
            return False


class ResourceCategory(db.Model):
    __tablename__ = 'resource_category'
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey(
        ThrivResource.id), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey(Category.id), nullable=False)
    resource = db.relationship(ThrivResource, backref='resource_categories')
    category = db.relationship(Category, backref='category_resources')


class ThrivType(db.Model):
    __tablename__ = 'type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    resources = db.relationship(
        'ThrivResource', backref=db.backref('type', lazy=True))
    icon_id = db.Column(db.Integer, db.ForeignKey('icon.id'))
    icon = db.relationship("Icon")


class ThrivSegment(db.Model):
    __tablename__ = 'segment'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    resources = db.relationship(
        'ThrivResource', backref=db.backref('segment', lazy=True))


class UploadedFile(db.Model):
    __tablename__ = 'uploaded_file'
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String)
    display_name = db.Column(db.String)
    date_modified = db.Column(db.DateTime)
    mime_type = db.Column(db.String)
    size = db.Column(db.Integer)
    md5 = db.Column(db.String)
    url = db.Column(db.String)
    resource_id = db.Column(
        db.Integer, db.ForeignKey(ThrivResource.id), nullable=True)
    resource = db.relationship(ThrivResource)


class User(db.Model):
    __tablename__ = 'ithriv_user'
    id = db.Column(db.Integer, primary_key=True)
    eppn = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=False, unique=True)
    display_name = db.Column(db.String)
    _password = db.Column('password', db.Binary(60))
    role = db.Column(db.String, default='User')
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    institution_id = db.Column('institution_id', db.Integer(),
                               db.ForeignKey('institution.id'))
    institution = db.relationship('ThrivInstitution')
    institutional_role = db.Column(db.String)
    division = db.Column(db.String)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)

    def is_correct_password(self, plaintext):
        if not self._password:
            raise RestException(RestException.LOGIN_FAILURE)
        return bcrypt.check_password_hash(self._password, plaintext)

    def encode_auth_token(self):
        try:
            iat = datetime.datetime.utcnow()
            exp = iat + datetime.timedelta(hours=2, minutes=0, seconds=0)
            payload = {'exp': exp, 'iat': iat, 'sub': self.id}
            return jwt.encode(
                payload, app.config.get('SECRET_KEY'), algorithm='HS256')
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        try:
            payload = jwt.decode(
                auth_token, app.config.get('SECRET_KEY'), algorithms='HS256')
            return payload['sub']
        except jwt.ExpiredSignatureError:
            raise RestException(RestException.TOKEN_EXPIRED)
        except jwt.InvalidTokenError:
            raise RestException(RestException.TOKEN_INVALID)


class Search():
    query = ""
    filters = []
    total = 0
    resources = []
    facets = []
    start = 0
    size = 0
    sort = None

    def __init__(self, query="", filters=[], start=0, size=10, sort=None):
        self.query = query
        self.filters = filters
        self.start = start
        self.size = size
        self.sort = sort

    def jsonFilters(self):
        jfilter = {}
        for f in self.filters:
            jfilter[f.field] = f.value

        return jfilter


class Facet():
    field = ""
    facetCounts = []

    def __init__(self, field):
        self.field = field


class FacetCount():
    def __init__(self, category, hit_count, is_selected):
        self.category = category
        self.hit_count = hit_count
        self.is_selected = is_selected


class Filter():
    field = ""
    value = ""

    def __init__(self, field, value):
        self.field = field
        self.value = value


class NotificationStatus(enum.Enum):
    unread = 'unread'
    read = 'read'
    action_taken = 'action_taken'


# Re-usable list of actions a user can take in response to a notification
# Examples:
# - Signing an agreement
# - Approving another user's request
# - Confirming upload or download of HSD
class NotificationAction(db.Model):
    __tablename__ = 'notification_action'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)
    date_created = db.Column(db.DateTime, default=datetime.datetime.now)
    last_updated = db.Column(db.DateTime, default=datetime.datetime.now)
    title = db.Column(db.String)
    description = db.Column(db.String)
    url = db.Column(db.String)


class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    date_created = db.Column(db.DateTime, default=datetime.datetime.now)
    last_updated = db.Column(db.DateTime, default=datetime.datetime.now)
    expiration_date = db.Column(db.DateTime, nullable=True)

    # list of NotificationAction sent to user
    actions = db.relationship('NotificationActionSent', uselist=True, backref='notification')

    # id of user receiving notification
    user_id = db.Column(db.Integer, db.ForeignKey('ithriv_user.id'))
    status = db.Column(db.Enum(NotificationStatus), default=NotificationStatus.unread)

    # NotificationAction taken by user
    action_taken = db.relationship('NotificationActionTaken', backref='notification')


# NotificationActions sent to user (i.e., list of possible actions user can take)
# Association (a.k.a. Bridge) table relating Notifications to NotificationActions
class NotificationActionSent(db.Model):
    __tablename__ = 'notification_action_sent'
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notification.id'))
    notification_action_id = db.Column(db.Integer, db.ForeignKey('notification_action.id'))
    date_notification_sent = db.Column(db.DateTime, default=datetime.datetime.now)


# NotificationAction taken by user
# Association (a.k.a. Bridge) table relating Notifications to NotificationAction
class NotificationActionTaken(db.Model):
    __tablename__ = 'notification_action_taken'
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notification.id'), nullable=True)
    notification_action_id = db.Column(db.Integer, db.ForeignKey('notification_action.id'), nullable=True)
    date_action_taken = db.Column(db.DateTime, default=datetime.datetime.now)
