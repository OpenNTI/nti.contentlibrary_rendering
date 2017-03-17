#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.security.interfaces import IParticipation

from nti.contentlibrary.interfaces import IRenderableContentPackage

from nti.contentlibrary_rendering.common import dump
from nti.contentlibrary_rendering.common import unpickle

from nti.contentrendering.plastexids import patch_all

from nti.coremetadata.interfaces import IRedisClient

from nti.externalization.proxy import removeAllProxies

from nti.ntiids.ntiids import find_object_with_ntiid

# Patch our plastex early.
patch_all()


def redis_client():
    return component.queryUtility(IRedisClient)


@interface.implementer(IParticipation)
class Participation(object):

    __slots__ = (b'interaction', b'principal')

    def __init__(self, principal):
        self.interaction = None
        self.principal = principal


def hset_item(job_id, item, queue, expiry=None):
    try:
        redis = redis_client()
        if redis is not None:
            data = dump(item)
            pipe = redis.pipeline()
            pipe.hset(queue, job_id, data)
            if expiry:
                pipe.expire(job_id, expiry)
            pipe.execute()
            return True
    except Exception:
        logger.exception("Could not place %s in %s for %s",
                         item, queue, job_id)
    return False


def hget_item(job_id, queue):
    try:
        redis = redis_client()
        if redis is not None:
            data = redis.hget(queue, job_id)
            if data is not None:
                return unpickle(data)
    except Exception:
        logger.exception("Could not get item from %s for %s",
                         queue, job_id)
    return None


def get_package(render_job):
    ntiid = render_job.PackageNTIID
    package = find_object_with_ntiid(ntiid)
    package = removeAllProxies(package)
    if package is None:
        raise ValueError("Package not found", ntiid)
    elif not IRenderableContentPackage.providedBy(package):
        raise TypeError("Invalid content package", ntiid)
    return package
