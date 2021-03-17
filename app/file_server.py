import boto3


class FileServer:

    def __init__(self, app):
        self.s3 = boto3.resource('s3')
        self.bucket = app.config['S3']['bucket']
        self.base_url = app.config['S3']['base_url']
        self.base_path = app.config['S3']['base_path']

    def _save_file(self, data, filename, mime_type):
        try:
            self.s3.Bucket(self.bucket).put_object(Key=filename, Body=data, ACL='public-read',
                                                   ContentType=mime_type)
            remote_path = self._get_remote_path(filename)
            return remote_path
        except Exception as e:
            print('could not put file into AWS S3 bucket.')

    def _get_remote_path(self, filename):
        return "{0}/{1}/{2}".format(self.base_url, self.bucket, filename)

    def save_icon(self, data, icon, file_extension, mime_type):
        path = "%s/ithriv/icon/%s.%s" % (self.base_path, icon.id, file_extension)
        print('save_icon path', path)
        try:
            file_name = self._save_file(data, path, mime_type)
            return file_name
        except Exception as e:
            print('could not save file.')

    def get_key(self, file):
        extension = file.file_name.split('.', 1)[1].lower()
        return "%s/ithriv/resource/attachment/%s.%s" % (self.base_path, file.id, extension)

    def save_file(self, data, file, mime_type):
        key = self.get_key(file)
        file_name = self._save_file(data, key, mime_type)
        return file_name

    def delete_file(self, file):
        key = self.get_key(file)
        self.s3.Object(self.bucket, key).delete()
