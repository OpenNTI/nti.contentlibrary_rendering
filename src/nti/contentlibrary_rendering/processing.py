#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zc.blist import BList

from zope import component

from zope.component.hooks import getSite
from zope.component.hooks import site as current_site

from nti.async import create_job

from nti.contentlibrary_rendering import CONTENT_UNITS_QUEUE

from nti.contentlibrary_rendering import get_factory

from nti.contentlibrary_rendering.common import get_site
from nti.contentlibrary_rendering.common import get_render_job

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.dataserver.interfaces import IDataserver

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.site.site import get_site_for_site_names

from nti.site.transient import TrivialSite

#: The max number of times we'll retry a job that is not found.
MAX_RETRY_COUNT = 3


def _dataserver_folder():
    dataserver = component.getUtility(IDataserver)
    return dataserver.root_folder['dataserver2']


def _do_execute_render_job( func, job_id=None, package_ntiid=None, retry_count=0,
                            *args, **kwargs):
    render_job = get_render_job(package_ntiid, job_id)
    if render_job is None:
        site_name = getSite().__name__
        package = find_object_with_ntiid( package_ntiid )
        meta = IContentPackageRenderMetadata( package, None )
        keys = ''
        if meta:
            keys = tuple(meta)
        if retry_count < MAX_RETRY_COUNT:
            # Re-queue; this may happen because of a race condition of when we open
            # the db connection (tx) and then pull from the redisqueue.
            # It's hard to distinguish between this case and when an object is
            # deleted before this job runs. Unfortunately, this job goes to the end
            # of the queue, but if we hit this race condition, the queue should be
            # nearly empty.
            logger.info('[%s] Job missing (deleted?); will retry. (%s) (%s)',
                        site_name,
                        job_id,
                        package_ntiid)
            retry_count += 1
            put_render_job(CONTENT_UNITS_QUEUE,
                           func,
                           job_id=job_id,
                           package_ntiid=package_ntiid,
                           retry_count=retry_count,
                           **kwargs)
        else:
            logger.info('[%s] Job missing (deleted?); event dropped. (%s) (%s) (retry_count=%s) (%s) (jobs=%s)',
                        site_name,
                        job_id,
                        package_ntiid,
                        retry_count,
                        package,
                        keys)
        return
    return func(render_job, *args, **kwargs)


def _do_execute_generic_job(*args, **kwargs):
    args = BList(args)
    func = args.pop(0)
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


def put_render_job(queue_name, func, job_id=None, *args, **kwargs):
    site = get_site()
    queue = get_job_queue(queue_name)
    job = create_job(_execute_render_job,
                     func,
                     job_id=job_id,
                     site_name=site,
                     *args, **kwargs)
    job.id = job_id
    queue.put(job)
    return job


def add_to_queue(queue_name, func, obj, **kwargs):
    return put_render_job(queue_name,
                          func,
                          job_id=obj.JobId,
                          package_ntiid=obj.PackageNTIID,
                          **kwargs)


def queue_add(name, func, obj, **kwargs):
    """
    We expect a `IContentPackageRenderJob` here.
    """
    return add_to_queue(name, func, obj, **kwargs)
queue_modified = queue_add


def queue_removed(queue_name, func, obj, job_id=None, **kwargs):
    """
    Queue up a job to remove package data.
    """
    site = get_site()
    queue = get_job_queue(queue_name)
    job = create_job(_execute_generic_job,
                     func,
                     obj,
                     site_name=site,
                     **kwargs)
    job.id = job_id
    queue.put(job)
    return job
