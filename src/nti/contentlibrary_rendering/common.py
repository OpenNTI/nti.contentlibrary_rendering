#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import six
import uuid
import zlib
import hashlib
import binascii
import tempfile
from io import BytesIO
from datetime import datetime
from six.moves import cPickle as pickle

import isodate

from zope import component
from zope import interface

from zope.component.hooks import getSite

from zope.security.interfaces import IParticipation

from nti.contentlibrary import AUTHORED_PREFIX

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.coremetadata.interfaces import IRedisClient

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.publishing.interfaces import IPublishable

from nti.site.interfaces import IHostPolicyFolder

from nti.traversal.location import find_interface

TMP_MAX = 10000

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IParticipation)
class Participation(object):

    __slots__ = ('interaction', 'principal')

    def __init__(self, principal):
        self.interaction = None
        self.principal = principal


def redis_client():
    return component.queryUtility(IRedisClient)


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


def mkdtemp(tmpdir=None):
    tmpdir = tmpdir or tempfile.gettempdir()
    for _ in range(TMP_MAX):
        digest = str(uuid.uuid4())[10:].upper().replace('-', '')
        digest = "%s_%s" % (AUTHORED_PREFIX, digest)
        path = os.path.join(tmpdir, digest)
        if not os.path.exists(path):
            os.makedirs(path)
            return path
    raise IOError("No usable temporary directory name found")


def is_published(obj):
    return not IPublishable.providedBy(obj) or obj.is_published()
isPublished = is_published


def get_site(site_name=None, context=None):
    if not site_name and context is not None:
        folder = find_interface(context, IHostPolicyFolder)
        site_name = getattr(folder, '__name__', None)
    if not site_name:
        site = getSite()
        site_name = site.__name__ if site is not None else None
    return site_name


def datetime_isoformat(now=None):
    now = now or datetime.now()
    return isodate.datetime_isoformat(now)


def object_finder(doc_id):
    return find_object_with_ntiid(doc_id)


def get_render_job(package_ntiid, job_id):
    """
    Get a render job from the given package_ntiid and job_id.
    """
    package = find_object_with_ntiid(package_ntiid)
    meta = IContentPackageRenderMetadata(package, None)
    try:
        result = meta[job_id]
    except (KeyError, TypeError, AttributeError):
        result = None
    return result


def get_creator(context):
    result = getattr(context, 'creator', context)
    result = getattr(result, 'username', result)
    result = getattr(result, 'id', result)  # check 4 principal
    return result


def dump(context):
    bio = BytesIO()
    pickle.dump(context, bio)
    bio.seek(0)
    result = zlib.compress(bio.read())
    return result


def unpickle(data):
    data = zlib.decompress(data)
    bio = BytesIO(data)
    bio.seek(0)
    result = pickle.load(bio)
    return result
