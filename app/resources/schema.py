from flask_marshmallow.sqla import ModelSchema
from marshmallow import fields, post_load
from sqlalchemy import func

from app import ma, db
from app.models import Availability, Notification, NotificationAction, NotificationActionSent, NotificationActionTaken
from app.models import Category
from app.models import Icon
from app.models import ThrivInstitution
from app.models import ThrivResource
from app.models import ResourceCategory
from app.models import Filter, Search
from app.models import ThrivType
from app.models import ThrivSegment
from app.models import UploadedFile
from app.models import User
from app.models import Favorite


class ThrivInstitutionSchema(ModelSchema):
    class Meta:
        model = ThrivInstitution
        fields = ('id', 'name', 'description', 'hide_availability')
    hide_availability = fields.Boolean(allow_none=True)


class IconSchema(ModelSchema):
    class Meta:
        model = Icon
        fields = ('id', 'name', 'url')


class ThrivTypeSchema(ModelSchema):
    class Meta:
        model = ThrivType
        fields = ('id', 'name', 'icon_id', 'icon')
    icon_id = fields.Integer(required=False, allow_none=True)
    icon = fields.Nested(IconSchema,  allow_none=True, dump_only=True)


class ThrivSegmentSchema(ModelSchema):
    class Meta:
        model = ThrivSegment
        fields = ('id', 'name')


class AvailabilitySchema(ModelSchema):
    class Meta:
        model = Availability
        fields = ('id', 'institution_id', 'resource_id',
                  'available', 'institution')
    institution = fields.Nested(
        ThrivInstitutionSchema(), dump_only=True, allow_none=True)


class FavoriteSchema(ModelSchema):
    class Meta:
        model = Favorite
        fields = ('id', 'resource_id', 'user_id', '_links')
    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.favoriteendpoint', id='<id>'),
    })


class ParentCategorySchema(ModelSchema):
    """Provides a view of the parent category, all the way to the top, but ignores children"""
    class Meta:
        model = Category
        fields = ('id', 'name', 'parent', 'level', 'color', 'icon_id',
                  'icon', 'image', '_links', 'brief_description',
                  'description', 'display_order')
    parent = fields.Nested('self', dump_only=True)
    level = fields.Function(lambda obj: obj.calculate_level())
    color = fields.Function(lambda obj: obj.calculate_color())
    icon_id = fields.Integer(required=False, allow_none=True)
    icon = fields.Nested(IconSchema, allow_none=True, dump_only=True)
    image = fields.String(required=False, allow_none=True)
    display_order = fields.Integer(
        required=True, allow_none=False, default=999)
    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.categoryendpoint', id='<id>'),
        'collection': ma.URLFor('api.categorylistendpoint'),
        'resources': ma.URLFor('api.resourcebycategoryendpoint', category_id='<id>')
    })


class CategoriesOnResourceSchema(ModelSchema):
    class Meta:
        model = ResourceCategory
        fields = ('id', '_links', 'resource_id', 'category_id', 'category')
    category = fields.Nested(ParentCategorySchema, dump_only=True)
    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.resourcecategoryendpoint', id='<id>'),
        'category': ma.URLFor('api.categoryendpoint', id='<category_id>'),
        'resource': ma.URLFor('api.resourceendpoint', id='<resource_id>')
    })


class FileSchema(ModelSchema):
    class Meta:
        model = UploadedFile
        fields = ('id', 'file_name', 'display_name', 'date_modified',
                  'mime_type', 'size', 'md5', 'resource_id', 'url')
    id = fields.Integer(required=False, allow_none=True)
    resource_id = fields.Integer(required=False, allow_none=True)


class ThrivResourceSchema(ModelSchema):
    class Meta:
        model = ThrivResource
        fields = ('id', 'name', 'description', 'last_updated', 'owner',
                  'website', 'cost', 'institution_id', 'type_id', 'type', 'segment_id', 'segment',
                  'institution', 'availabilities', 'approved', 'files',
                  'contact_email', 'contact_phone', 'contact_notes', 'private',
                  '_links', 'favorites', 'favorite_count', 'resource_categories',
                  'owners', 'user_may_view', 'user_may_edit', 'location', 'starts', 'ends')
    id = fields.Integer(required=False, allow_none=True)
    last_updated = fields.Date(required=False, allow_none=True)
    owner = fields.String(required=False, allow_none=True)
    contact_email = fields.String(required=False, allow_none=True)
    contact_phone = fields.String(required=False, allow_none=True)
    contact_notes = fields.String(required=False, allow_none=True)
    website = fields.String(required=False, allow_none=True)
    institution_id = fields.Integer(required=False, allow_none=True)
    type_id = fields.Integer(required=False, allow_none=True)
    segment_id = fields.Integer(required=False, allow_none=True)
    approved = fields.String(required=False, allow_none=True)
    favorite_count = fields.Integer(required=False, allow_none=True)
    private = fields.Boolean(required=False, allow_none=True)
    location = fields.String(required=False, allow_none=True)
    starts = fields.DateTime(required=False, allow_none=True)
    ends = fields.DateTime(required=False, allow_none=True)

    type = fields.Nested(ThrivTypeSchema(), dump_only=True)
    segment = fields.Nested(ThrivSegmentSchema(), dump_only=True)
    institution = fields.Nested(
        ThrivInstitutionSchema(), dump_only=True, allow_none=True)
    availabilities = fields.Nested(
        AvailabilitySchema(), many=True, dump_only=True)
    favorites = fields.Nested(FavoriteSchema(), many=True, dump_only=True)
    resource_categories = fields.Nested(
        CategoriesOnResourceSchema(), many=True, dump_only=True)
    files = fields.Nested(FileSchema(), many=True, dump_only=True)
    owners = fields.Method('get_owners', dump_only=True)
    user_may_view = fields.Method('get_user_may_view', dump_only=True)
    user_may_edit = fields.Method('get_user_may_edit', dump_only=True)
    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.resourceendpoint', id='<id>'),
        'collection': ma.URLFor('api.resourcelistendpoint'),
        'institution': ma.UrlFor('api.institutionendpoint', id='<institution_id>'),
        'type': ma.UrlFor('api.typeendpoint', id='<type_id>'),
        'categories': ma.UrlFor('api.categorybyresourceendpoint', resource_id='<id>'),
        'availability': ma.UrlFor('api.resourceavailabilityendpoint', resource_id='<id>')
    },
        dump_only=True)

    def get_owners(self, obj):
        if callable(obj.owners):
            return obj.owners() if isinstance(obj, ThrivResource) else []
        else:
            return obj.owners

    def get_user_may_view(self, obj):
        if callable(obj.user_may_view):
            return obj.user_may_view() if isinstance(obj, ThrivResource) else False
        else:
            return obj.user_may_view

    def get_user_may_edit(self, obj):
        if callable(obj.user_may_edit):
            return obj.user_may_edit() if isinstance(obj, ThrivResource) else False
        else:
            return obj.user_may_edit


class CategorySchema(ModelSchema):
    """Provides detailed information about a category, including all the children"""
    class Meta:
        model = Category
        fields = ('id', 'name', 'brief_description', 'description',
                  'color', 'level', 'image', 'icon_id', 'icon',
                  'children', 'parent_id', 'parent', 'resource_count',
                  'display_order', '_links')
    id = fields.Integer(required=False, allow_none=True)
    icon_id = fields.Integer(required=False, allow_none=True)
    icon = fields.Nested(IconSchema,  allow_none=True, dump_only=True)
    image = fields.String(required=False, allow_none=True)
    parent_id = fields.Integer(required=False, allow_none=True)
    children = fields.Nested(
        'self', many=True, dump_only=True, exclude=('parent', 'color'))
    parent = fields.Nested(ParentCategorySchema, dump_only=True)
    color = fields.Function(lambda obj: obj.calculate_color())
    level = fields.Function(lambda obj: obj.calculate_level(), dump_only=True)
    resource_count = fields.Method('get_resource_count')
    display_order = fields.Integer(
        required=False, allow_none=False, default=999)
    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.categoryendpoint', id='<id>'),
        'collection': ma.URLFor('api.categorylistendpoint'),
        'resources': ma.URLFor('api.resourcebycategoryendpoint', category_id='<id>')
    })

    def get_resource_count_for_current_user(self, obj):
        """This takes the current users viewable resources into account, but is a little too slow."""
        category_resources = obj.category_resources
        resource_count = 0
        for cr in category_resources:
            if cr.resource.user_may_view():
                resource_count += 1
        return resource_count

    def get_resource_count(self, obj):
        query = db.session.query(ResourceCategory).join(ResourceCategory.resource)\
            .filter(ResourceCategory.category_id == obj.id).filter(ThrivResource.approved == 'Approved')
        count_q = query.statement.with_only_columns(
            [func.count()]).order_by(None)
        return query.session.execute(count_q).scalar()


class ResourceCategoriesSchema(ModelSchema):
    class Meta:
        model = ResourceCategory
        fields = ('id', '_links', 'resource_id', 'category_id', 'category')
    category = fields.Nested(CategorySchema, dump_only=True)
    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.resourcecategoryendpoint', id='<id>'),
        'category': ma.URLFor('api.categoryendpoint', id='<category_id>'),
        'resource': ma.URLFor('api.resourceendpoint', id='<resource_id>')
    })


class CategoryResourcesSchema(ModelSchema):
    class Meta:
        model = ResourceCategory
        fields = ('id', '_links', 'resource_id', 'category_id', 'resource')
    resource = fields.Nested(ThrivResourceSchema, dump_only=True)
    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.resourcecategoryendpoint', id='<id>'),
        'category': ma.URLFor('api.categoryendpoint', id='<category_id>'),
        'resource': ma.URLFor('api.resourceendpoint', id='<resource_id>')
    })


class ResourceCategorySchema(ModelSchema):
    class Meta:
        model = ResourceCategory
        fields = ('id', '_links', 'resource_id', 'category_id')
    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.resourcecategoryendpoint', id='<id>'),
        'category': ma.URLFor('api.categoryendpoint', id='<category_id>'),
        'resource': ma.URLFor('api.resourceendpoint', id='<resource_id>')
    })


class UserFavoritesSchema(ModelSchema):
    class Meta:
        model = Favorite
        fields = ('id', 'user_id', 'resource_id', 'resource', '_links')
    resource = fields.Nested(ThrivResourceSchema, dump_only=True)
    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.favoriteendpoint', id='<id>'),
        'user': ma.URLFor('api.userendpoint', id='<user_id>'),
        'resource': ma.URLFor('api.resourceendpoint', id='<resource_id>')
    })


class SearchSchema(ma.Schema):

    class FilterSchema(ma.Schema):
        field = fields.Str()
        value = fields.Raw()

        @post_load
        def make_filter(self, data):
            return Filter(**data)

    class FacetSchema(ma.Schema):

        class FacetCountSchema(ma.Schema):
            category = fields.Str()
            hit_count = fields.Integer()
            is_selected = fields.Boolean()

        field = fields.Str()
        facetCounts = ma.List(ma.Nested(FacetCountSchema))

    query = fields.Str()
    start = fields.Integer()
    size = fields.Integer()
    sort = fields.Str()
    filters = ma.List(ma.Nested(FilterSchema))
    total = fields.Integer(dump_only=True)
    resources = fields.List(fields.Dict(), dump_only=True)
    facets = ma.List(ma.Nested(FacetSchema), dump_only=True)
    ordered = True

    @post_load
    def make_search(self, data):
        return Search(**data)


class UserSchema(ModelSchema):
    class Meta:
        model = User
        fields = ('id', '_links', 'eppn', 'display_name', 'email', 'role', 'institution_id',
                  'institution', 'password', 'institutional_role', 'division')
    password = fields.String(load_only=True)
    id = fields.Integer(required=False, allow_none=True)
    institution_id = fields.Integer(required=False, allow_none=True)
    institution = fields.Nested(
        ThrivInstitutionSchema(), dump_only=True, allow_none=True)

    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.userendpoint', id='<id>'),
        'favorites': ma.UrlFor('api.userfavoriteendpoint'),
        'resources': ma.UrlFor('api.userresourceendpoint'),
    })


class UserSearchSchema(ma.Schema):
    pages = fields.Integer()
    total = fields.Integer()
    items = ma.List(ma.Nested(UserSchema))


class NotificationActionSchema(ModelSchema):
    class Meta:
        model = NotificationAction
        fields = ('id', 'type', 'date_created', 'last_updated', 'title', 'description', 'url')


class NotificationActionSentSchema(ModelSchema):
    class Meta:
        model = NotificationActionSent
        fields = ('id', 'notification_id', 'notification_action_id', 'date_notification_sent', 'notification_action')
    notification_action = fields.Nested(NotificationActionSchema(), dump_only=True)


class NotificationActionTakenSchema(ModelSchema):
    class Meta:
        model = NotificationActionTaken
        fields = ('id', 'notification_id', 'notification_action_id', 'date_action_taken', 'notification_action')
    notification_action = fields.Nested(NotificationActionSchema(), dump_only=True)


class NotificationSchema(ModelSchema):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'description', 'date_created', 'last_updated', 'expiration_date',
                  'actions', 'user_id', 'status', 'action_taken')
    actions = fields.List(fields.Nested(NotificationActionSentSchema()), dump_only=True)
    action_taken = fields.Nested(NotificationActionTakenSchema(), dump_only=True, allow_none=True)

