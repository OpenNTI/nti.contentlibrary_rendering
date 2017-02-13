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

from nti.contentlibrary_rendering import get_factory

from nti.contentlibrary_rendering.common import get_site
from nti.contentlibrary_rendering.common import get_render_job

from nti.dataserver.interfaces import IDataserver

from nti.site.site import get_site_for_site_names

from nti.site.transient import TrivialSite


def _dataserver_folder():
    dataserver = component.getUtility(IDataserver)
    return dataserver.root_folder['dataserver2']


def _do_execute_job(*args, **kwargs):
    args = BList(args)
    func = args.pop(0)
    package_ntiid = kwargs.pop('package_ntiid')
    job_id = kwargs.pop('job_id')
    render_job = get_render_job(package_ntiid, job_id)
    if render_job is None:
        logger.info(
            'Job missing (deleted?) before event could be processed; event dropped. (%s) (%s) (%s)',
            job_id, package_ntiid, func)
        return
    return func(render_job, *args, **kwargs)


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


def _execute_job(*args, **kwargs):
    """
    Performs the actual execution of a job.  We'll attempt to do
    so in the site the event occurred in, otherwise, we'll run in
    whatever site we are currently in.
    """
    event_site_name = kwargs.pop('site_name', None)
    event_site = _get_job_site(event_site_name)
    with current_site(event_site):
        return _do_execute_job(*args, **kwargs)


def get_job_queue(name):
    factory = get_factory()
    return factory.get_queue(name)


def put_job(queue_name, func, job_id=None, *args, **kwargs):
    queue = get_job_queue(queue_name)
    job = create_job(_execute_job, func, job_id=job_id, *args, **kwargs)
    job.id = job_id
    queue.put(job)
    return job


def add_to_queue(queue_name, func, obj, **kwargs):
    site = get_site()
    return put_job(queue_name,
                   func,
                   package_ntiid=obj.PackageNTIID,
                   job_id=obj.JobId,
                   site_name=site, **kwargs)


def queue_add(name, func, obj, **kwargs):
    """
    We expect a `IContentPackageRenderJob` here.
    """
    return add_to_queue(name, func, obj, **kwargs)


def queue_modified(name, func, obj, **kwargs):
    """
    We expect a `IContentPackageRenderJob` here.
    """
    return add_to_queue(name, func, obj, **kwargs)
