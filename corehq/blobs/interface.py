from __future__ import absolute_import
from __future__ import unicode_literals
import re
from abc import ABCMeta, abstractmethod

from . import DEFAULT_BUCKET
from .metadata import MetaDB
import six

SAFENAME = re.compile("^[a-z0-9_./{}-]+$", re.IGNORECASE)
NOT_SET = object()


class AbstractBlobDB(six.with_metaclass(ABCMeta, object)):
    """Storage interface for large binary data objects

    The constructor of this class creates a `MetaDB` instance for managing
    blob metadata, so it is important that subclass constructors call it.
    """

    def __init__(self):
        self.metadb = MetaDB()

    @abstractmethod
    def put(self, content, identifier=None, bucket=DEFAULT_BUCKET, **blob_meta_args):
        """Put a blob in persistent storage

        :param content: A file-like object in binary read mode.
        :param identifier: DEPRECATED
        :param bucket: DEPRECATED
        :param **blob_meta_args: A single `"meta"` argument (`BlobMeta`
        object) or arguments used to construct a `BlobMeta` object:

        - domain - (required, text) domain name.
        - parent_id - (required, text) parent identifier, used for
        sharding.
        - type_code - (required, int) blob type code. See
        `corehq.blobs.CODES`.
        - key - (optional, text) globally unique blob identifier. A
        new key will be generated with `uuid4().hex` if missing or
        `None`. This is the key used to store the blob in the external
        blob store.
        - name - (optional, text) blob name.
        - content_length - (optional, int) content length. Will be
        calculated from the given content if not given.
        - content_type - (optional, text) content type.
        - timeout - minimum number of minutes the object will live in
        the blobdb. `None` means forever. There are no guarantees on the
        maximum time it may live in blob storage.

        :returns: A `BlobMeta` object. The returned object has a
        `key` attribute that may be used to get or delete the blob.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, identifier=None, bucket=DEFAULT_BUCKET, key=None):
        """Get a blob

        :param identifier: DEPRECATED
        :param bucket: DEPRECATED
        :param key: Blob key.
        :returns: A file-like object in binary read mode. The returned
        object should be closed when finished reading.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self, identifier=None, bucket=DEFAULT_BUCKET, key=None):
        """Check if blob exists

        :param identifier: DEPRECATED
        :param bucket: DEPRECATED
        :param key: Blob key.
        :returns: True if the object exists else false.
        """
        raise NotImplementedError

    @abstractmethod
    def size(self, identifier=None, bucket=DEFAULT_BUCKET, key=None):
        """Gets the size of a blob in bytes

        :param identifier: DEPRECATED
        :param bucket: DEPRECATED
        :param key: Blob key.
        :returns: The number of bytes of a blob
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, identifier=NOT_SET, bucket=NOT_SET, key=None):
        """Delete a blob

        :param identifier: DEPRECATED
        :param bucket: DEPRECATED
        :param key: Blob key.
        :returns: True if the blob was deleted else false. None if it is
        not known if the blob was deleted or not.
        """
        raise NotImplementedError

    @abstractmethod
    def bulk_delete(self, paths=None, metas=None):
        """Delete multiple blobs.

        :param paths: DEPRECATED
        :param metas: The list of `BlobMeta` objects for blobs to delete.
        :returns: True if all the blobs were deleted else false. `None` if
        it is not known if the blob was deleted or not.
        """
        raise NotImplementedError

    @abstractmethod
    def copy_blob(self, content, info=None, bucket=None, key=None):
        """Copy blob from other blob database

        :param info: DEPRECATED
        :param bucket: DEPRECATED
        :param content: File-like blob content object.
        :param key: Blob key.
        """
        raise NotImplementedError

    @staticmethod
    def get_args_for_delete(identifier=NOT_SET, bucket=NOT_SET):
        if identifier is NOT_SET and bucket is NOT_SET:
            raise TypeError("'identifier' and/or 'bucket' is required")
        if identifier is None:
            raise TypeError("refusing to delete entire bucket when "
                            "null blob identifier is provided (either "
                            "provide a real blob identifier or pass "
                            "bucket as keyword argument)")
        if identifier is NOT_SET:
            assert bucket is not NOT_SET
            identifier = None
        elif bucket is NOT_SET:
            bucket = DEFAULT_BUCKET
        return identifier, bucket
