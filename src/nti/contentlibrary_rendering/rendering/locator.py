#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os

from zope import component

from zope.security.interfaces import IPrincipal

from zope.security.management import endInteraction
from zope.security.management import newInteraction
from zope.security.management import restoreInteraction

from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator

from nti.contentlibrary_rendering.processing import add_to_queue

from nti.contentlibrary_rendering.rendering import dump
from nti.contentlibrary_rendering.rendering import get_package
from nti.contentlibrary_rendering.rendering import Participation

from nti.contentlibrary_rendering.rendering.sync import sync_package_job


def locate_rendered_content(package, output_dir):
    path, name = os.path.split(output_dir)
    name_noe, unused = os.path.splitext(name)
    path = os.path.join(path, name_noe)
    # locate
    locator = component.getUtility(IRenderedContentLocator)
    result = locator.locate(path, package)
    return result


def process_render_job(render_job, output_dir):
    package = get_package(render_job)
    result = locate_rendered_content(package, package)
    render_job.OutputRoot = result  # save
    return result


def place_next_job(render_job, bucket):
    bucket = dump(bucket)
    add_to_queue("sync_queue",
                 sync_package_job,
                 render_job,
                 bucket=bucket)


def locate_package_job(render_job, output_dir):
    logger.info('Locating content (%s) (%s)',
                render_job.PackageNTIID,
                render_job.job_id)
    job_id = render_job.job_id
    creator = render_job.creator
    endInteraction()
    try:
        newInteraction(Participation(IPrincipal(creator)))
        bucket = process_render_job(render_job)
        place_next_job(render_job, bucket)
    except Exception as e:
        # XXX: Do we want to fail all applicable jobs?
        logger.exception('Render job %s failed', job_id)
        render_job.update_to_failed_state(str(e))
    finally:
        restoreInteraction()
