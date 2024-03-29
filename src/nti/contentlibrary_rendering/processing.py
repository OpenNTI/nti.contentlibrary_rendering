#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=keyword-arg-before-vararg

from zope import component

from zope.component.hooks import getSite
from zope.component.hooks import site as current_site

from nti.asynchronous import create_job

from nti.contentlibrary_rendering import get_factory

from nti.contentlibrary_rendering.common import get_site
from nti.contentlibrary_rendering.common import get_render_job

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.coremetadata.interfaces import IDataserver

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.site.site import get_site_for_site_names

from nti.site.transient import TrivialSite

logger = __import__('logging').getLogger(__name__)


def _dataserver_folder():
    dataserver = component.getUtility(IDataserver)
    return dataserver.root_folder['dataserver2']


def _handle_missing_job(job_id, package_ntiid):
    site_name = getSite().__name__
    package = find_object_with_ntiid(package_ntiid)
    meta = IContentPackageRenderMetadata(package, None)
    keys = tuple(meta) if meta else ''
    logger.info('[%s] Job missing (deleted?); event dropped. (%s) (%s) (%s) (jobs=%s)',
                site_name,
                job_id,
                package_ntiid,
                package,
                keys)


def _do_execute_render_job(func, job_id=None, package_ntiid=None,
                           *args, **kwargs):
    render_job = get_render_job(package_ntiid, job_id)
    if render_job is None:
        _handle_missing_job(job_id, package_ntiid)
    elif render_job.is_finished():
        # Job preemptively completed.
        logger.info('[%s] Job already completed, ignoring (%s) (%s)',
                    getSite().__name__,
                    job_id,
                    package_ntiid)
    else:
        # Ok, we can process this one.
        return func(render_job, *args, **kwargs)


def _do_execute_generic_job(*args, **kwargs):
    func, args = args[0], args[1:]
    return func(*args, **kwargs)


def _get_job_site(job_site_name=None):
    old_site = getSite()
    if job_site_name is None:
        job_site = old_site
    else:
        ds_folder = _dataserver_folder()
        with current_site(ds_folder):
            job_site = get_site_for_site_names((job_site_name,))

        if job_site is None or isinstance(job_site, TrivialSite):
            raise ValueError('No site found for (%s)' % job_site_name)
    return job_site


def _execute_job(job_runner, *args, **kwargs):
    """
    Performs the actual execution of a job.  We'll attempt to do
    so in the site the event occurred in, otherwise, we'll run in
    whatever site we are currently in.
    """
    event_site_name = kwargs.pop('site_name', None)
    event_site = _get_job_site(event_site_name)
    with current_site(event_site):
        return job_runner(*args, **kwargs)


def _execute_render_job(*args, **kwargs):
    return _execute_job(_do_execute_render_job, *args, **kwargs)


def _execute_generic_job(*args, **kwargs):
    return _execute_job(_do_execute_generic_job, *args, **kwargs)


def get_job_queue(name):
    factory = get_factory()
    return factory.get_queue(name)


def put_render_job(queue_name, func, job_id=None, site_name=None, *args, **kwargs):
    site_name = get_site(site_name)
    queue = get_job_queue(queue_name)
    job = create_job(_execute_render_job,
                     func,
                     job_id=job_id,
                     site_name=site_name,
                     *args, **kwargs)
    job.id = job_id
    queue.put(job)
    return job


def put_generic_job(queue_name, func, job_id=None, site_name=None, *args, **kwargs):
    site_name = get_site(site_name)
    queue = get_job_queue(queue_name)
    job = create_job(_execute_generic_job,
                     func,
                     job_id=job_id,
                     site_name=site_name,
                     *args, **kwargs)
    job.id = job_id
    queue.put(job)
    return job


def add_to_queue(queue_name, func, obj, site_name=None, **kwargs):
    return put_render_job(queue_name,
                          func,
                          job_id=obj.JobId,
                          package_ntiid=obj.PackageNTIID,
                          site_name=site_name,
                          **kwargs)


def queue_add(name, func, obj, **kwargs):
    """
    We expect a `IContentPackageRenderJob` here.
    """
    return add_to_queue(name, func, obj, **kwargs)


def queue_modified(name, func, obj, **kwargs):
    queue_add(name, func, obj, **kwargs)


def queue_removed(queue_name, func, obj, job_id=None, site_name=None, **kwargs):
    """
    Queue up a job to remove package data.
    """
    site = get_site(site_name, obj)
    queue = get_job_queue(queue_name)
    job = create_job(_execute_generic_job,
                     func,
                     obj,
                     site_name=site,
                     **kwargs)
    job.id = job_id
    queue.put(job)
    return job
