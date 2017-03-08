#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import six
import time
import shutil
import socket
import hashlib
import binascii

import boto

from zope import component
from zope import interface

from zope.cachedescriptors.property import readproperty

from zope.component.hooks import site as getSite
from zope.component.hooks import site as current_site

from zope.intid.interfaces import IIntIds

from nti.contentlibrary.filesystem import FilesystemBucket

from nti.contentlibrary.interfaces import IContentPackageLibrary
from nti.contentlibrary.interfaces import IDelimitedHierarchyContentPackageEnumeration

from nti.contentlibrary.nti_s3put import IGNORED_DOTFILES

from nti.contentlibrary.nti_s3put import get_key_name
from nti.contentlibrary.nti_s3put import s3_upload_file

from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator

from nti.property.property import Lazy

from nti.site.hostpolicy import get_host_site

from nti.site.interfaces import IHostPolicyFolder

from nti.traversal.traversal import find_interface


def hex_encode(raw_bytes):
    if not isinstance(raw_bytes, six.binary_type):
        raise TypeError("Argument must be raw bytes: got %r" %
                        type(raw_bytes).__name__)
    result = binascii.b2a_hex(raw_bytes)
    return result


def sha1_digest(*inputs):
    hash_func = hashlib.sha1()
    for i in inputs:
        if not isinstance(i, six.binary_type):
            raise TypeError("Input type must be bytes: got %r" % 
                            type(i).__name__)
        hash_func.update(i)
    return hash_func.digest()


def sha1_hex_digest(*inputs):
    return hex_encode(sha1_digest(*inputs))


@interface.implementer(IRenderedContentLocator)
class LocatorMixin(object):

    @Lazy
    def _intids(self):
        return component.getUtility(IIntIds)

    def _get_id(self, context):
        return str(self._intids.getId(context))

    def _do_locate(self, path, root, context):
        pass

    def _do_remove(self, root, context):
        pass

    def _hex(self, intid, now=None):
        now = now or time.time()
        digest = sha1_hex_digest(six.binary_type(intid), 
                                 six.binary_type(now),
                                 six.binary_type(socket.gethostname()))
        return digest[20:].upper() # 40 char string

    def locate(self, path, context):
        # validate
        if not os.path.exists(path):
            raise OSError("'%s' does not exists" % path)
        if not os.path.isdir(path):
            raise OSError("'%s' is not a directory" % path)
        # move using use package site
        folder = find_interface(context, IHostPolicyFolder, strict=False)
        with current_site(get_host_site(folder.__name__)):
            library = component.getUtility(IContentPackageLibrary)
            enumeration = IDelimitedHierarchyContentPackageEnumeration(library)
            return self._do_locate(path, enumeration.root, context)

    def remove(self, bucket):
        logger.info("Removing bucket (%s)", bucket.absolute_path)
        return self._do_remove(bucket)


@interface.implementer(IRenderedContentLocator)
class FilesystemLocator(LocatorMixin):

    def _move(self, source, destination):
        # Make the destination so perms are correct.
        if not os.path.isdir(destination):
            os.makedirs(destination)

        for child in os.listdir(source):
            dest_path = os.path.join(destination, child)
            source_path = os.path.join(source, child)
            shutil.move(source_path, dest_path)
        shutil.rmtree(source, ignore_errors=True)

    def _do_locate(self, path, root, context):
        assert isinstance(root, FilesystemBucket)
        intid = self._get_id(context)
        name = "authored_%s.%s" % (intid, self._hex(intid))
        child = root.getChildNamed(name)
        if child is not None:
            logger.warn("Removing %s", child)
            destination = child.absolute_path
            shutil.rmtree(child.absolute_path)
        else:
            destination = os.path.join(root.absolute_path, name)
        self._move(path, destination)
        return root.getChildNamed(name)

    def _do_remove(self, bucket):
        shutil.rmtree(bucket.absolute_path)


@interface.implementer(IRenderedContentLocator)
class S3Locator(LocatorMixin):

    prefix = '/'
    headers = {}
    grant = 'public-read-write'

    @readproperty
    def settings(self):
        return os.environ

    @readproperty
    def aws_access_key_id(self):
        return self.settings.get('AWS_ACCESS_KEY_ID')

    @readproperty
    def aws_secret_access_key(self):
        return self.settings.get('AWS_SECRET_ACCESS_KEY')

    @readproperty
    def bucket_name(self):
        return getSite().__name__

    def _connection(self, debug=True):
        connection = boto.connect_s3(aws_access_key_id=self.aws_access_key_id,
                                     aws_secret_access_key=self.aws_secret_access_key)
        connection.debug = debug
        return connection

    def _transfer(self, path, bucket_name, prefix='/', headers=None, debug=True):
        headers = dict() if headers is None else headers
        connection = self._connection(debug)
        bucket = connection.get_bucket(bucket_name)
        for dirpath, _, files in os.walk(path):
            for filename in files:
                if filename in IGNORED_DOTFILES:
                    continue

                fullpath = os.path.join(dirpath, filename)
                key_name = get_key_name(fullpath, prefix)
                if debug:
                    logger.info('Copying %s to %s/%s',
                                filename, bucket_name, key_name)

                key = bucket.new_key(key_name)
                file_headers = s3_upload_file(key,
                                              fullpath,
                                              gzip_types=(),
                                              headers=headers,
                                              policy=self.grant)

                if debug:
                    logger.info('Copied %s to %s/%s as type %s encoding %s',
                                filename, bucket_name, key_name,
                                file_headers.get(
                                    'Content-Type',
                                    'application/octet-stream'),
                                file_headers.get('Content-Encoding', 'identity'))
        connection.close()
        return bucket

    def _do_locate(self, path, root, context, debug=True):
        prefix = self.prefix
        jobname = str(self._intids.getId(context))
        if path.endswith(jobname):
            # e.g. /tmp/render/12000 get /tmp/render
            prefix = os.path.split(path)[0]
        return self._transfer(path, self.bucket_name,
                              debug=debug,
                              prefix=prefix,
                              headers=self.headers)

    def _do_remove(self, bucket, debug=True):
        prefix = str(bucket.name)
        connection = self._connection(debug)
        try:
            bucket = connection.get_bucket(self.bucket_name)
            keys = [k.name for k in bucket.list(prefix=prefix)]
            if keys:
                bucket.delete_keys(keys)
        except Exception:
            logger.exception("Could not remove '%s/*' files in bucket %s",
                             prefix, self.bucket_name)
            return False
        finally:
            connection.close()
        return True
