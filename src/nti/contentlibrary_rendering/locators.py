#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import stat
import shutil

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

    def _update_perms(self, file):
        """
        We shouldn't have to do this, but make sure our perms for the
        output dir retain our parent group id as well as give RW access
        to both user and (copied) group.
        """
        parent = os.path.dirname(file)
        parent_stat = os.stat(parent)
        parent_gid = parent_stat.st_gid
        # -1 unchanged
        os.chown( file, -1, parent_gid)
        os.chmod( file,
                  stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                  stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |
                  stat.S_IROTH)

    def _do_locate(self, path, root, context):
        assert isinstance(root, FilesystemBucket)
        intid = self._get_id(context)
        child = root.getChildNamed(intid)
        if child is not None:
            logger.warn("Removing %s", child)
            destination = child.absolute_path
            shutil.rmtree(child.absolute_path)
        else:
            destination = os.path.join(root.absolute_path, intid)
        shutil.move(path, destination)
        self._update_perms(destination)
        return root.getChildNamed(intid)

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
