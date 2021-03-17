import sys

import magic
from flask import json

from app.models import Availability
from app.models import Category
from app.models import EmailLog
from app.models import Icon
from app.models import ThrivResource
from app.models import ThrivInstitution
from app.models import ResourceCategory
from app.models import ThrivType
from app.models import ThrivSegment
from app.models import Favorite
from app import db, elastic_index, file_server
import csv

from app.models import User
from app.resources.schema import CategorySchema


class DataLoader:
    """Loads CSV files into the database"""

    def __init__(self, directory="./example_data"):
        self.resource_file = directory + "/resources.csv"
        self.availability_file = directory + "/resource_availability.csv"
        self.category_file = directory + "/categories.csv"
        self.resource_category_file = directory + "/resource_categories.csv"
        self.icon_file = directory + "/icons.csv"
        self.user_file = directory + "/users.csv"
        self.user_favorite_file = directory + "/user_favorites.csv"
        self.institution_file = directory + "/institutions.csv"
        self.mime = magic.Magic(mime=True)
        print("Data loader initialized")

    def load_resources(self):
        with open(self.resource_file, newline='') as csvfile:
            reader = csv.reader(
                csvfile, delimiter=csv.excel.delimiter, quotechar=csv.excel.quotechar)
            next(reader, None)  # skip the headers
            for index, row in enumerate(reader):
                segment_type = self.get_segment_by_name(
                    row[11]) if row[11] else None
                resource_type=self.get_type_by_name(
                    row[3]) if row[3] else None
                institution=self.get_inst_by_name(row[2])
                resource=ThrivResource(id = row[0], name = row[1], description = row[10], segment = segment_type, type = resource_type, institution = institution,
                                         owner = row[8], website = row[9], contact_notes = row[4])
                resource.approved="Approved" if (
                    index % 2 == 0) else "Unapproved"
                resource.private=(index % 3 == 0)
                db.session.add(resource)
            print("Resources loaded.  There are now %i resources in the database." %
                  db.session.query(ThrivResource).count())
        db.session.commit()
        db.session.execute("SELECT setval('resource_id_seq', "
                           "COALESCE((SELECT MAX(id) + 1 FROM resource), 1), false);")
        db.session.commit()

    def load_availability(self):
        with open(self.availability_file, newline='') as csvfile:
            reader = csv.reader(
                csvfile, delimiter=csv.excel.delimiter, quotechar=csv.excel.quotechar)
            header = next(reader, None)  # use headers to set availability

            for row in reader:
                try:
                    resource = self.get_resource_by_id(row[0])
                    resource.cost = row[10]
                except:
                    print(
                        "Warning:  Availability references non existing resource id %s, Ignoring." % row[0])
                    continue
                for i in range(3, 9):
                    is_available = row[i].lower().strip(
                    ) == "yes" or row[i].lower().strip() == "true"
                    institution = self.get_inst_by_name(header[i])
                    availability = Availability(resource=resource, institution_id=institution.id,
                                                available=is_available)
                    db.session.add(availability)
            db.session.commit()
            print("Availability loaded.  There are now %i availability records in the database." %
                  db.session.query(Availability).count())

    def load_icons(self):
        with open(self.icon_file, newline='') as csvfile:
            reader = csv.reader(
                csvfile, delimiter=csv.excel.delimiter, quotechar=csv.excel.quotechar)
            header = next(reader, None)  # use headers to set availability
            for row in reader:
                id = eval(row[0])
                icon = db.session.query(Icon).filter(Icon.id == id).first()
                if icon is None:
                    icon = Icon(id=id, name=row[1])
                path = "./example_data/icons/%s" % row[2]
                extension = path.rsplit('.', 1)[1].lower()
                mime_type = self.mime.from_file(path)
                data = open(path, 'rb')

                try:
                    icon.url = file_server.save_icon(data, icon, extension, mime_type)
                except Exception as e:
                    print('unable to save icon.')

                db.session.add(icon)

                resource_type = self.get_type_by_name(
                    row[3]) if row[3] else None
                if resource_type:
                    resource_type.icon = icon
                    db.session.add(resource_type)
        db.session.commit()

    def load_categories(self):
        with open(self.category_file, newline='') as csvfile:
            reader = csv.reader(
                csvfile, delimiter=csv.excel.delimiter, quotechar=csv.excel.quotechar)
            header = next(reader, None)  # use headers to set availability

            for row in reader:
                id = eval(row[0])
                category = Category(
                    id=id, brief_description=row[4], name=row[3],
                    description=row[5], color=row[7], image=row[8])
                if row[2] != '':
                    parent_id = eval(row[2])
                    category.parent_id = parent_id
                if row[6] != '':
                    icon_id = eval(row[6])
                    category.icon_id = icon_id
                if row[9] != '':
                    display_order = eval(row[9])
                    category.display_order = display_order
                db.session.add(category)
            # As we manually set the ids, we need to update the sequence manually as well.
            db.session.commit()
            db.session.execute("SELECT setval('category_id_seq', "
                               "COALESCE((SELECT MAX(id) + 1 FROM category), 1), false);")
            db.session.commit()
            print("Categories.  There are now %i category records in the database." %
                  db.session.query(Category).count())

    def load_resource_categories(self):
        with open(self.resource_category_file, newline='') as csvfile:
            reader = csv.reader(
                csvfile, delimiter=csv.excel.delimiter, quotechar=csv.excel.quotechar)
            next(reader, None)  # use headers to set availability

            for row in reader:
                for i in range(4, 10):
                    if not row[i]:
                        continue
                    resource_id = eval(row[0])
                    category_id = eval(row[i])

                    resource_category = ResourceCategory(resource_id=resource_id,
                                                         category_id=category_id)
                    db.session.add(resource_category)
            db.session.commit()
            print("There are now %i links between resources and categories in the database." %
                  db.session.query(ResourceCategory).count())

    def load_users(self):
        with open(self.user_file, newline='') as csvfile:
            reader = csv.reader(
                csvfile, delimiter=csv.excel.delimiter, quotechar=csv.excel.quotechar)
            next(reader, None)  # use headers to set availability

            for row in reader:
                user = User(id=row[0], eppn=row[1], email=row[1], display_name=row[2], password=row[3], role=row[4],
                            email_verified=True)

                db.session.add(user)
            db.session.commit()
            db.session.execute("SELECT setval('ithriv_user_id_seq', "
                               "COALESCE((SELECT MAX(id) + 1 FROM ithriv_user), 1), false);")
            db.session.commit()
            print("There are now %i users in the database." %
                  db.session.query(User).count())

    def load_institutions(self):
        with open(self.institution_file, newline='') as csvfile:
            reader = csv.reader(
                csvfile, delimiter=csv.excel.delimiter, quotechar=csv.excel.quotechar)
            next(reader, None)  # use headers to set availability

            for row in reader:
                inst = ThrivInstitution(
                    id=row[0], name=row[1], description=row[2], domain=row[3])
                if row[4] == 'True':
                    inst.hide_availability = True
                db.session.add(inst)
            db.session.commit()
            db.session.execute("SELECT setval('institution_id_seq', "
                               "COALESCE((SELECT MAX(id) + 1 FROM institution), 1), false);")
            db.session.commit()
            print("There are now %i institutions in the database." %
                  db.session.query(ThrivInstitution).count())

    def load_user_favorites(self):
        with open(self.user_favorite_file, newline='') as csvfile:
            reader = csv.reader(
                csvfile, delimiter=csv.excel.delimiter, quotechar=csv.excel.quotechar)
            next(reader, None)  # use headers to set availability

            for row in reader:
                for i in range(1, 7):
                    if not row[i]:
                        continue
                    user_id = eval(row[0])
                    resource_id = eval(row[i])

                    user_favorite = Favorite(user_id=user_id,
                                             resource_id=resource_id)
                    db.session.add(user_favorite)
            db.session.commit()
            print("Favorites Loaded. There are now %i links between users and resources in the database." %
                  db.session.query(Favorite).count())

    def get_resource_by_id(self, id):
        resource = db.session.query(ThrivResource).filter(
            ThrivResource.id == id).first()
        if resource is None:
            raise(Exception("No resource found with id: %s" % id))
        return resource

    def get_type_by_name(self, type_name):
        type = db.session.query(ThrivType).filter(
            ThrivType.name == type_name).first()
        if (type == None):
            type = ThrivType(name=type_name)
            db.session.add(type)
        return type

    def get_inst_by_name(self, inst_name):
        institution = db.session.query(ThrivInstitution).filter(
            ThrivInstitution.name == inst_name).first()
        if (institution == None):
            institution = ThrivInstitution(name=inst_name)
            db.session.add(institution)
        return institution

    def get_segment_by_name(self, segment_name):
        segment = db.session.query(ThrivSegment).filter(
            ThrivSegment.name == segment_name).first()
        if (segment == None):
            segment = ThrivSegment(name=segment_name)
            db.session.add(segment)
        return segment

    def build_index(self):
        elastic_index.load_resources(db.session.query(ThrivResource).all())

    def clear_index(self):
        print("Clearing the index")
        elastic_index.clear()

    def clear(self):
        db.session.query(ResourceCategory).delete()
        db.session.query(Availability).delete()
        db.session.query(Favorite).delete()
        db.session.query(ThrivResource).delete()
        db.session.query(ThrivType).delete()
        db.session.query(Category).delete()
        db.session.query(EmailLog).delete()
        db.session.query(User).delete()
        db.session.query(ThrivInstitution).delete()
        db.session.commit()
