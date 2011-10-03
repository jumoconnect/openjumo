from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.s3 import connection, key as s3key
from django.conf import settings
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.db import models
import Image
import os, math, re, tempfile
import uuid


class ImageType:
    USER = "user"
    ORG = "org"
    ISSUE = "issue"
    MEDIAITEM = "mediaitem"
    MISC = "misc"

class ImageSize:
    LARGE = "large"
    SMALL = "small"


MEDIAITEM_WIDTH_LARGE = 400
MEDIAITEM_WIDTH_SMALL = 161
EVERYTHING_ELSE_LARGE = 150
EVERYTHING_ELSE_SMALL = 50


#Leaving this for user model. We can change it to work like org issue later.
def upload_user_image(opened_image, id, size_name, width, height):
    file_path = '%s/%s/%s' % (ImageType.USER, id, size_name)
    crop = True if width == height else False
    image = _resize_image(opened_image, width, crop)
    url = _upload_photo(image, ImageType.USER, file_path=file_path)
    return (url, image.size[0], image.size[1])

#Temporarily adding this back in so upload_user_image can work. Will remove this
#when user img urls are refactored to use S3EnabledImageField
def _upload_photo(image, image_type, id=None, file_path=None):
    conn = connection.S3Connection(settings.AWS_ACCESS_KEY, settings.AWS_SECRET_KEY)
    s3bucket = conn.create_bucket(settings.AWS_PHOTO_UPLOAD_BUCKET)
    filename = str(uuid.uuid4())

    tmp = tempfile.NamedTemporaryFile('w+b', -1, '.jpg')
    image = image.convert("RGB")
    image.save(tmp.name)

    key = s3key.Key(s3bucket)
    if file_path:
      key.key = '%s.jpg' % file_path
    elif id:
      key.key = '%s/%s_%s.jpg' % (image_type, filename, id)
    else:
      key.key = '%s/%s.jpg' % (image_type, filename)
    try:
      key.set_contents_from_filename(tmp.name, None, True, None, 10, 'public-read', None)
    except:
      raise
    key.close()
    tmp.close()
    return "http://%s.s3.amazonaws.com/%s" % (settings.AWS_PHOTO_UPLOAD_BUCKET, key.key)

def _resize_image(image, max_width, crop = False):
    if max_width is None or max_width == 0:
        return image.convert('RGB')

    if crop:
        x = image.size[0]
        y = image.size[1]
        if x != y:
          box = (0, 0, x, y)
          if x > y:
            crop_1 = int(math.floor((x-y) / 2))
            crop_2 = int(math.ceil((x-y) / 2))
            box = (crop_1, 0, x - crop_2, y)
          else:
            crop_1 = int(math.floor((y-x) / 2))
            crop_2 = int(math.ceil((y-x) / 2))
            box = (0, crop_1, x, y - crop_2)
          image = image.crop(box)

    ratio = (max_width/float(image.size[0]))
    max_height = int((float(image.size[1]) * float(ratio)))
    image = image.convert('RGB')
    if image.size[0] > max_width:
        image = image.resize((max_width, max_height), Image.ANTIALIAS)
    return image




#I want to move all this to forms...not the model.
class S3ImageStorage(FileSystemStorage):
    inst_id = uuid.uuid4()
    def __init__(self, bucket_name=None, image_type = ImageType.MISC, image_size=ImageSize.LARGE):
        self.image_type = image_type
        self.image_size = image_size
        self.bucket_name = bucket_name
        self._bucket = None

    def _open(self, name, mode='rb'):
        class S3File(File):
            def __init__(self, key):
                self.key = key

            def size(self):
                return self.key.size

            def read(self, *args, **kwargs):
                return self.key.read(*args, **kwargs)

            def write(self, content):
                self.key.set_contents_from_string(content)

            def close(self):
                self.key.close()

        return S3File(Key(self.bucket, name))

    def _build_filepath(self):
        return "%s/%s_%s.jpg" % (self.image_type, self.inst_id, self.image_size)

    def _save(self, name, content):
        name = self._build_filepath()
        content.seek(0)
        image = _resize_image(Image.open(content), self.image_width, self.should_image_crop)
        tmp = tempfile.NamedTemporaryFile("w+b", -1, '.jpg')
        image.save(tmp.name)

        key = Key(self.bucket, name)
        key.set_contents_from_filename(tmp.name, None, True, None, 10, 'public-read', None)

        return name

    @property
    def bucket(self):
        if self._bucket == None:
            self.connection = S3Connection(settings.AWS_ACCESS_KEY, settings.AWS_SECRET_KEY)
            if not self.connection.lookup(self.bucket_name):
                self.connection.create_bucket(self.bucket_name)
            self._bucket = self.connection.get_bucket(self.bucket_name)
        return self._bucket

    @property
    def image_width(self):
        #Right now it's only determined by size but might be type and more later
        #We can do complicated mapping when that time comes.
        if self.image_size == ImageSize.LARGE:
            if self.image_type == ImageType.MEDIAITEM:
                return MEDIAITEM_WIDTH_LARGE
            else:
                return EVERYTHING_ELSE_LARGE

        if self.image_type == ImageType.MEDIAITEM:
            return MEDIAITEM_WIDTH_SMALL

        return EVERYTHING_ELSE_SMALL

    @property
    def should_image_crop(self):
        if self.image_type == ImageType.MEDIAITEM:
            return False
        if self.image_size == ImageSize.LARGE:
            return False
        return True

    def delete(self, name):
        self.bucket.delete_key(name)

    def exists(self, name):
        return Key(self.bucket, name).exists()

    def listdir(self, path):
        return [key.name for key in self.bucket.list()]

    def path(self, name):
        raise NotImplementedError

    def size(self, name):
        return self.bucket.get_key(name).size

    def url(self, name):
        try:
            return Key(self.bucket, name).generate_url(100000)
        except KeyError:
            return None
    
    def get_available_name(self, name):
        return name

class S3EnabledImageField(models.ImageField):
    def __init__(self, bucket_name=settings.AWS_PHOTO_UPLOAD_BUCKET, image_type=ImageType.MISC, image_size=ImageSize.LARGE, **kwargs):
        kwargs['storage'] = S3ImageStorage(bucket_name, image_type=image_type, image_size=image_size)
        kwargs['upload_to'] = "ignore_this"
        super(S3EnabledImageField, self).__init__(**kwargs)
