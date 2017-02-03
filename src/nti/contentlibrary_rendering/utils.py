#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Event listeners.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.contentlibrary_rendering import CONTENT_UNITS_QUEUE

from nti.contentlibrary_rendering.common import is_published

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.contentlibrary_rendering.processing import queue_add
from nti.contentlibrary_rendering.processing import queue_modified

from nti.contentlibrary_rendering._render import render_package_job

def _create_render_job(package, user):
    meta = IContentPackageRenderMetadata(package)
    job = meta.createJob(package, user)
    return job

def render_package(package, user):
    """
    Render the given package. This may not be performed synchronously.
    """
    job = _create_render_job(package, user)
    queue_add(CONTENT_UNITS_QUEUE, render_package_job, job)

def render_modified_package(package, user):
    """
    Render the updated package (if published). This may not be performed synchronously.
    """
    job = _create_render_job(package, user)
    if is_published(package):
        queue_modified(CONTENT_UNITS_QUEUE, render_package_job, job)
