#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.contentlibrary.interfaces import IRenderableContentPackage

from nti.contentlibrary_rendering import NTI_PROVIDER
from nti.contentlibrary_rendering import CONTENT_UNITS_QUEUE

from nti.contentlibrary_rendering._render import render_package_job

from nti.contentlibrary_rendering.common import get_site
from nti.contentlibrary_rendering.common import is_published

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.contentlibrary_rendering.unpublish import queue_remove_rendered_package

from nti.contentlibrary_rendering.processing import queue_add
from nti.contentlibrary_rendering.processing import queue_modified

logger = __import__('logging').getLogger(__name__)


def _create_render_job(package, user, provider=NTI_PROVIDER, mark_rendered=True):
    meta = IContentPackageRenderMetadata(package)
    # pylint: disable=too-many-function-args
    job = meta.createJob(package, user, provider, mark_rendered)
    return job


def render_package(package, user, provider=NTI_PROVIDER, mark_rendered=True):
    """
    Render the given package. This may not be performed synchronously.
    """
    if IRenderableContentPackage.providedBy(package):
        site_name = get_site(context=package)
        job = _create_render_job(package, user, provider, mark_rendered)
        queue_add(CONTENT_UNITS_QUEUE,
                  render_package_job,
                  job,
                  site_name=site_name)
        return job


def render_modified_package(package, user, provider=NTI_PROVIDER, mark_rendered=True):
    """
    Render the updated package (if published). This may not be performed synchronously.
    """
    job = _create_render_job(package, user, provider, mark_rendered)
    if IRenderableContentPackage.providedBy(package) and is_published(package):
        site_name = get_site(context=package)
        queue_modified(CONTENT_UNITS_QUEUE,
                       render_package_job,
                       job,
                       site_name=site_name)
    return job


def remove_rendered_package(package, root=None, site_name=None):
    if IRenderableContentPackage.providedBy(package):
        root = root \
            or getattr(package, 'root', None) \
            or getattr(package, 'key', None)
        if root is not None:
            site_name = get_site(site_name, context=package)
            queue_remove_rendered_package(package.ntiid, root, site_name)
