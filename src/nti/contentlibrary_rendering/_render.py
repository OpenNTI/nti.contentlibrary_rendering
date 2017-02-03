#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.contentlibrary.interfaces import IRenderableContentPackage

from nti.ntiids.ntiids import find_object_with_ntiid


def nti_render(tex_source):
    pass


def transform_content(package):
    pass


def _do_render_package(render_job):
    ntiid = render_job.PackageNTIID
    package = find_object_with_ntiid(ntiid)
    if package is None:
        raise Exception("Package not found", ntiid)
    elif not IRenderableContentPackage.providedBy(package):
        raise Exception("Invalid content package", ntiid)
    transform_content(package)


def render_package_job(render_job):
    job_id = render_job.job_id
    try:
        _do_render_package(render_job)
    except Exception as e:
        logger.exception('Render job %s failed', job_id)
        render_job.update_to_failed_state(str(e))
    else:
        render_job.update_to_success_state()
