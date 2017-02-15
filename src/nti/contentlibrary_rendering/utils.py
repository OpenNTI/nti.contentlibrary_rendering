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

from nti.contentlibrary_rendering._render import render_package_job

from nti.contentlibrary_rendering.common import is_published

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.contentlibrary_rendering.processing import queue_add
from nti.contentlibrary_rendering.processing import queue_modified


def _create_render_job(package, user, provider='NTI', mark_rendered=True):
    meta = IContentPackageRenderMetadata(package)
    job = meta.createJob(package, user, provider, mark_rendered)
    return job


def render_package(package, user, provider='NTI', mark_rendered=True):
    """
    Render the given package. This may not be performed synchronously.
    """
    job = _create_render_job(package, user, provider, mark_rendered)
    queue_add(CONTENT_UNITS_QUEUE, render_package_job, job)


def render_modified_package(package, user, provider='NTI', mark_rendered=True):
    """
    Render the updated package (if published). This may not be performed synchronously.
    """
    job = _create_render_job(package, user, provider, mark_rendered)
    if is_published(package):
        queue_modified(CONTENT_UNITS_QUEUE, render_package_job, job)
