#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator

from nti.contentlibrary_rendering import CONTENT_UNITS_QUEUE

from nti.contentlibrary_rendering.processing import queue_removed

logger = __import__('logging').getLogger(__name__)


def delete_package_data(bucket):
    locator = component.getUtility(IRenderedContentLocator)
    return locator.remove(bucket)


def remove_rendered_package(bucket):
    delete_package_data(bucket)


def queue_remove_rendered_package(ntiid, root, site_name=None):
    # Have to pass the bucket to the package remove function since
    # the package will no longer be resolvable outside this transaction.
    # This must be enough info to cleanup whatever needs to be cleaned up.
    job_id = "remover_%s_%s" % (ntiid, root.name)
    logger.info("Queuing remover job %s", root.name)
    queue_removed(CONTENT_UNITS_QUEUE,
                  remove_rendered_package,
                  root,
                  job_id=job_id,
                  site_name=site_name)
