import os

# Set environment variable to testing before loading.
# IMPORTANT - Environment must be loaded before app, models, etc....
os.environ["APP_CONFIG_FILE"] = '../config/testing.py'
os.environ["TESTING"] = "true"

from resources.schema import FileSchema
from sqlalchemy import or_
import base64
import datetime
import json
import math
import quopri
import re
import unittest

from app import app, db, elastic_index, data_loader
from app.models import Availability, UploadedFile, ThrivSegment, Category, Favorite, ThrivResource, ThrivType, \
    ThrivInstitution, User, Notification, NotificationStatus, NotificationAction, NotificationActionSent


def clean_db(database):
    database.session.commit()

    for table in reversed(database.metadata.sorted_tables):
        database.session.execute(table.delete())
        database.session.commit()


class BaseTest(unittest.TestCase):
    if not app.config['TESTING']:
        raise (Exception("INVALID TEST CONFIGURATION. This is almost always in import order issue."
                         "The first class to import in each test should be the base_test.py file."))

    test_eppn = "dhf8r@virginia.edu"
    admin_eppn = "dhf8admin@virginia.edu"

    @classmethod
    def setUpClass(cls):
        app.config.from_object('config.testing')
        cls.ctx = app.test_request_context()
        cls.app = app.test_client()
        cls.ctx.push()
        db.create_all()
        data_loader.DataLoader().build_index()

    @classmethod
    def tearDownClass(cls):
        db.drop_all()
        db.session.remove()
        data_loader.DataLoader().clear_index()

    def setUp(self):
        db.session.flush()
        self.ctx.push()
        clean_db(db)
        data_loader.DataLoader().clear_index()
        self.auths = {}

    def tearDown(self):
        db.session.rollback()
        self.ctx.pop()
        db.session.flush()

    def assertSuccess(self, rv):
        try:
            data = json.loads(rv.get_data(as_text=True))
            self.assertTrue(
                200 <= rv.status_code < 300,
                'BAD Response: %i. \n %s' % (rv.status_code, json.dumps(data)))
        except:
            self.assertTrue(
                200 <= rv.status_code < 300,
                'BAD Response: %i.' % rv.status_code)

    def construct_user(self,
                       id=421,
                       eppn="poe.resistance@rebels.org",
                       display_name="Poe Dameron",
                       email="poe.resistance@rebels.org",
                       role="User",
                       institution=None):
        u = User(
            id=id,
            eppn=eppn,
            display_name=display_name,
            email=email,
            role=role)

        if institution:
            u.institution_id = institution.id

        db.session.add(u)
        db.session.commit()

        db_user = db.session.query(User).filter_by(eppn=u.eppn).first()
        self.assertEqual(db_user.display_name, u.display_name)
        return db_user

    def construct_admin_user(self,
                             eppn="general.organa@rebels.org",
                             display_name="General Organa",
                             email="general.organa@rebels.org",
                             role="Admin",
                             institution=None):
        u = User(
            eppn=eppn,
            display_name=display_name,
            email=email,
            role=role)

        if institution:
            u.institution_id = institution.id

        db.session.add(u)
        db.session.commit()

        db_user = db.session.query(User).filter_by(eppn=u.eppn).first()
        self.assertIsNotNone(db_user)
        self.assertIsNotNone(db_user.id)
        self.assertEqual(db_user.display_name, u.display_name)
        self.assertEqual(db_user.role, 'Admin')

        if institution:
            self.assertEqual(db_user.institution_id, institution.id)

        return db_user

    def construct_various_users(self):
        users = [
            self.construct_user(
                id=123,
                eppn=self.test_eppn,
                display_name="Oscar the Grouch",
                email=self.test_eppn),
            self.construct_user(
                id=456,
                eppn=self.admin_eppn,
                display_name="Big Bird",
                email=self.admin_eppn,
                role="Admin"),
            self.construct_user(
                id=789,
                eppn="stuff123@vt.edu",
                display_name="Elmo",
                email="stuff123@vt.edu")
        ]

        db_users = []

        for user in users:
            db_user = db.session \
                .query(User) \
                .filter_by(display_name=user.display_name).first()
            self.assertEqual(db_user.email, user.email)
            db_users.append(db_user)

        self.assertEqual(len(db_users), len(users))
        return db_users

    def construct_institution(
            self,
            name="School for Exceptionally Talented Mynocks",
            domain="asete.edu",
            description="The asteroid's premiere exogorth parasite education",
            hide_availability=False,
    ):
        institution = ThrivInstitution(
            name=name, domain=domain, description=description, hide_availability=hide_availability)

        # Check database for existing institution
        existing_inst = db.session \
            .query(ThrivInstitution) \
            .filter(or_(
            (ThrivInstitution.name == name),
            (ThrivInstitution.domain == domain))).first()

        if not existing_inst:
            db.session.add(institution)
            db.session.commit()
            db_inst = db.session \
                .query(ThrivInstitution) \
                .filter_by(name=name).first()
        else:
            db_inst = existing_inst

        self.assertIsNotNone(db_inst)
        self.assertIsNotNone(db_inst.id)
        return db_inst

    def construct_type(self, name='Resource'):
        new_type = ThrivType(name=name)
        db.session.add(new_type)
        db_type = db.session.query(ThrivType).filter_by(name=name).first()
        self.assertIsNotNone(db_type)
        self.assertIsNotNone(db_type.id)
        return db_type

    def construct_segment(self, name='Resource'):
        segment = ThrivSegment(name=name)
        db.session.add(segment)
        db_segment = db.session.query(ThrivSegment).filter_by(name=name).first()
        self.assertIsNotNone(db_segment)
        self.assertIsNotNone(db_segment.id)
        return db_segment

    def construct_resource(self,
                           type_name="Starfighter",
                           institution=None,
                           name="T-70 X-Wing",
                           description="Small. Fast. Blows stuff up.",
                           owner="poe.resistance@rebels.org",
                           website="rebels.org",
                           cost='$100B credits',
                           available_to='UVA',
                           contact_email='poe.resistance@rebels.org',
                           contact_phone='111-222-3333',
                           contact_notes='I have a bad feeling about this.',
                           approved='Unapproved',
                           private=False,
                           segment_name='Resource'):
        type_obj = self.construct_type(type_name)

        if institution is None and available_to is not None:
            institution = self.construct_institution(name=available_to)

        segment = self.construct_segment(name=segment_name)

        resource = ThrivResource(
            name=name,
            description=description,
            type_id=type_obj.id,
            institution_id=institution.id,
            owner=owner,
            website=website,
            cost=cost,
            contact_email=contact_email,
            contact_phone=contact_phone,
            contact_notes=contact_notes,
            approved=approved,
            private=private,
            segment_id=segment.id,
        )
        db.session.add(resource)
        db.session.commit()

        if available_to is not None:
            availability = Availability(
                resource_id=resource.id, institution_id=institution.id, available=True)
            db.session.add(availability)
            db.session.commit()

            db_availability = db.session.query(Availability).filter_by(resource_id=resource.id).first()
            self.assertIsNotNone(db_availability)
            self.assertIsNotNone(db_availability.id)
            self.assertEqual(db_availability.institution_id, institution.id)


        db_resource = db.session.query(ThrivResource).filter_by(name=name).first()
        self.assertIsNotNone(db_resource)
        self.assertIsNotNone(db_resource.id)

        elastic_index.add_resource(db_resource)
        return db_resource

    def construct_various_resources(self, institution=None, owner=None):
        resources = []
        i1_name = "Binks College of Bantha Poodology"
        i1_domain = "first-order.mil"
        i2_name = "Organa School for Rebellious Orphans"
        i2_domain = "rebels.org"
        o1 = "kylo.ren@first-order.mil"
        o2 = "mon.mothma@rebels.org"

        if institution is not None:
            # Assign institution to half of the resources
            i1 = institution
        else:
            i1 = self.construct_institution(name=i1_name, domain=i1_domain)
        i2 = self.construct_institution(name=i2_name, domain=i2_domain)

        if owner is not None:
            # Assign owner to half of the resources
            o1 = owner

        resource_names = [
            "The Phantom of Menace", "The Clone Army Attacketh",
            "Tragedy of the Sith's Revenge", "Verily, A New Hope",
            "The Empire Striketh Back", "The Jedi Doth Return",
            "The Force Doth Awaken", "Jedi The Last",
            "The Ewok Quest of Courage's Caravan", "Hurlyburly for Endor",
            "Wars of Yonder Stars Midwinter's Celebration",
            "Cloning of the Soldiers", "Rebellion-Upon-Mandalore",
            "Resistance's Tale", "MacSolo", "Rogue The First"
        ]

        for index, name in enumerate(resource_names):
            n = index + 1
            r_approved = "Approved" if (n % 2 == 0) else "Unapproved"
            r_private = (math.ceil(n / 2) % 2 == 0)
            r_institution = i1 if (math.ceil(n / 4) % 2 == 0) else i2
            r_owner = o1 if (math.ceil(n / 8) % 2 == 0) else o2

            resource = self.construct_resource(
                name=name,
                approved=r_approved,
                private=r_private,
                institution=r_institution,
                owner=r_owner)

            resources.append(resource)

        return resources

    def construct_category(self,
                           name="Test Category",
                           description="A category to test with!",
                           parent=None,
                           display_order=None):
        category = Category(name=name, description=description)
        if parent is not None:
            category.parent = parent
        if display_order is not None:
            category.display_order = display_order
        db.session.add(category)
        return category

    def construct_favorite(self, user, resource):
        favorite = Favorite(user_id=user.id, resource_id=resource.id)
        db.session.add(favorite)
        db.session.commit()
        return favorite

    def construct_action(self, title="Die", description="You can die too, for all I care!",
                         action_type="Deny", url="https://as.you.wish.edu"):
        action = NotificationAction(title=title, description=description, type=action_type, url=url)
        db.session.add(action)
        db.session.commit()

        db_action = db.session.query(NotificationAction)\
            .filter(NotificationAction.title == title)\
            .filter(NotificationAction.description == description)\
            .first()

        self.assertIsNotNone(db_action)
        self.assertIsNotNone(db_action.id)

        return db_action

    def construct_notification(self, title="No more rhymes now, I mean it!",
                               description="Anybody want a peanut?", user=None, actions=None):
        if user is None:
            user = self.construct_user()

        if actions is None:
            action1 = self.construct_action(
                title="Blave",
                description="To blave means to bluff. So you're probably playing cards, and he cheated.",
                action_type="Deny",
                url="https://liar.liar.liiaaarrr.gov"
            )
            action2 = self.construct_action(
                title="Love",
                description="Sonny, true love is the greatest thing in the world -- except for a nice MLT",
                action_type="Approve",
                url="https://humiliations.galore.edu"
            )
            actions = [action1, action2]

        notification = Notification(title=title, description=description, user_id=user.id)
        db.session.add(notification)
        db.session.commit()

        db_notification = db.session.query(Notification)\
            .filter(Notification.title == title)\
            .filter(Notification.description == description)\
            .filter(Notification.user_id == user.id)\
            .first()

        self.assertIsNotNone(db_notification)
        self.assertIsNotNone(db_notification.id)
        self.assertEqual(db_notification.status, NotificationStatus.unread)

        for action in actions:
            notification_action_sent = NotificationActionSent(
                notification_id=db_notification.id,
                notification_action_id=action.id
            )
            db.session.add(notification_action_sent)
            db.session.commit()

        return db_notification

    def search(self, query, user=None):
        """Executes a query as the given user, returning the resulting search results object."""
        rv = self.app.post(
            '/api/search',
            data=json.dumps(query),
            follow_redirects=True,
            content_type="application/json",
            headers=self.logged_in_headers(user))
        self.assertSuccess(rv)
        return json.loads(rv.get_data(as_text=True))

    def search_anonymous(self, query):
        """Executes a query as an anonymous user, returning the resulting search results object."""
        rv = self.app.post(
            '/api/search',
            data=json.dumps(query),
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        return json.loads(rv.get_data(as_text=True))

    def searchUsers(self, query, user=None):
        '''Executes a query, returning the resulting search results object.'''
        rv = self.app.get(
            '/api/user',
            query_string=query,
            follow_redirects=True,
            content_type="application/json",
            headers=self.logged_in_headers(user=user))
        self.assertSuccess(rv)
        return json.loads(rv.get_data(as_text=True))

    def addFile(self,
                file_name='happy_coconuts.svg',
                display_name='Happy Coconuts',
                md5="3399"):
        file = UploadedFile(
            file_name=file_name,
            display_name=display_name,
            date_modified=datetime.datetime.now(),
            md5=md5)
        rv = self.app.post(
            '/api/file',
            data=json.dumps(FileSchema().dump(file).data),
            content_type="application/json")
        return rv

    def decode(self, encoded_words):
        """
        Useful for checking the content of email messages
        (which we store in an array for testing)
        """
        encoded_word_regex = r'=\?{1}(.+)\?{1}([b|q])\?{1}(.+)\?{1}='
        charset, encoding, encoded_text = re.match(encoded_word_regex,
                                                   encoded_words).groups()
        if encoding is 'b':
            byte_string = base64.b64decode(encoded_text)
        elif encoding is 'q':
            byte_string = quopri.decodestring(encoded_text)
        text = byte_string.decode(charset)
        text = text.replace("_", " ")
        return text

    def logged_in_headers(self, user=None):
        # If no user is provided, generate a dummy Admin user
        if not user:
            user = User(
                eppn=self.admin_eppn,
                display_name="Admin",
                email=self.admin_eppn,
                role="Admin")

        # Add institution if it's not already in database
        domain = user.email.split("@")[1]
        institution = self.construct_institution(name=domain, domain=domain)

        # Add user if it's not already in database
        if user.eppn:
            existing_user = User.query.filter_by(eppn=user.eppn).first()
        if not existing_user and user.email:
            existing_user = User.query.filter_by(email=user.email).first()

        if not existing_user:
            user.institution_id = institution.id
            db.session.add(user)
            db.session.commit()

        headers = {
            'eppn': user.eppn,
            'givenName': user.display_name,
            'mail': user.email
        }

        rv = self.app.get(
            "/api/login",
            headers=headers,
            follow_redirects=True,
            content_type="application/json")

        db_user = User.query.filter_by(eppn=user.eppn).first()
        return dict(
            Authorization='Bearer ' + db_user.encode_auth_token().decode())

    def create_user_with_password(self, display_name="Peter Dinklage", eppn="tyrion@got.com",
                                       email="tyrion@got.com", role="User", password="peterpass"):
        data = {
            "display_name": display_name,
            "eppn": eppn,
            "email": email,
            "role": role
        }
        rv = self.app.post(
            '/api/user',
            data=json.dumps(data),
            follow_redirects=True,
            headers=self.logged_in_headers(),
            content_type="application/json")
        self.assertSuccess(rv)
        user = User.query.filter_by(eppn=eppn).first()
        user.password = password
        db.session.add(user)
        db.session.commit()

        rv = self.app.get(
            '/api/user/%i' % user.id,
            content_type="application/json",
            headers=self.logged_in_headers())
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(display_name, response["display_name"])
        self.assertEqual(email, response["email"])
        self.assertEqual(role, response["role"])
        self.assertEqual(True, user.is_correct_password(password))
        return user

    def login_user(self, display_name="Kit Harington", eppn="jonsnow@got.com",
                                       email="jonsnow@got.com", role="User", password="y0ukn0wn0th!ng"):
        user = self.create_user_with_password(display_name=display_name, eppn=eppn,
                                       email=email, role=role, password=password)
        data = {"email": email, "password": password}

        # Login shouldn't work with email not yet verified
        rv = self.app.post(
            '/api/login_password',
            data=json.dumps(data),
            content_type="application/json")
        self.assertEqual(400, rv.status_code)

        user.email_verified = True
        rv = self.app.post(
            '/api/login_password',
            data=json.dumps(data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertIsNotNone(response["token"])

        return user

    def logout_user(self, display_name="Emilia Clarke", eppn="daeneryst@got.com",
                                       email="daeneryst@got.com", role="User", password="5t0rmb0r~"):
        user = self.login_user(display_name=display_name, eppn=eppn,
                                       email=email, role=role, password=password)
        rv = self.app.delete('/api/session',
            content_type="application/json",
            headers=self.logged_in_headers(user))
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertIsNone(response)

        return user
