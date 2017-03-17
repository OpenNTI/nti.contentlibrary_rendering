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
from zope import lifecycleevent

from zope.annotation.interfaces import IAnnotations

from zope.event import notify as event_notify

from zope.security.interfaces import IPrincipal

from zope.security.management import endInteraction
from zope.security.management import newInteraction
from zope.security.management import restoreInteraction

from nti.contentlibrary.interfaces import IContentUnit
from nti.contentlibrary.interfaces import IContentPackage
from nti.contentlibrary.interfaces import IContentRendered
from nti.contentlibrary.interfaces import IContentPackageLibrary
from nti.contentlibrary.interfaces import IEclipseContentPackageFactory

from nti.contentlibrary.interfaces import ContentPackageRenderedEvent
from nti.contentlibrary.interfaces import ContentPackageLocationChanged

from nti.contentlibrary.library import register_content_units
from nti.contentlibrary.library import unregister_content_units

from nti.contentlibrary.zodb import RenderableContentUnit
from nti.contentlibrary.zodb import RenderableContentPackage

from nti.contentlibrary_rendering.common import unpickle

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.contentlibrary_rendering.rendering import get_package
from nti.contentlibrary_rendering.rendering import Participation


def copy_attributes(source, target, names):
    for name in names or ():
        value = getattr(source, name, None)
        if value is not None:
            setattr(target, name, value)


def _copy_annotations(package, old_annotations):
    """
    Copy our old annotations into our new package (with new ntiid).
    """
    # This means we have a staled/orphaned annotation object now
    new_annotations = IAnnotations(package)
    if old_annotations is None or old_annotations is new_annotations:
        return
    for key, value in old_annotations.items():
        new_annotations[key] = value


def copy_package_data(item, target):
    """
    copy rendered data to target
    """
    factory = IEclipseContentPackageFactory(item)
    package = factory.new_instance(item,
                                   RenderableContentPackage,
                                   RenderableContentUnit)
    assert package is not None, "Invalid rendered content directory"

    # 1. copy all new content package attributes
    copy_attributes(package, target, IContentPackage.names())

    # 2 copy unit attributes
    attributes = set(IContentUnit.names()) - {'children', 'ntiid', 'icon'}
    copy_attributes(package, target, attributes)

    # 3. copy icon
    if not target.icon and package.icon:
        target.icon = package.icon

    # 4. copy displayable content attributes
    copy_attributes(package, target, ('PlatformPresentationResources',))

    # 5. unregister from the intid facility the target old children
    for unit in target.children or ():
        unregister_content_units(unit)

    # 6. register with the intid facility the new children
    target.children = target.children_iterable_factory(package.children or ())
    register_content_units(target, target)

    # 7. register target package in the library to populate internal
    # structures
    library = component.queryUtility(IContentPackageLibrary)
    if library is not None and target.children:
        library.add(target, event=False)

    return target


def copy_and_notify(bucket, package, render_job):
    old_root = package.root

    # 4. copy from target
    copy_package_data(bucket, package)

    # 5. marked as rendered
    if render_job.MarkRendered:
        interface.alsoProvides(package, IContentRendered)
        event_notify(ContentPackageRenderedEvent(package))

    if old_root is not None:
        event_notify(ContentPackageLocationChanged(package, old_root, bucket))

    # marked changed
    lifecycleevent.modified(package)
    return package


def get_metadata(context):
    return IContentPackageRenderMetadata(context, None)


def get_jobs_to_update(render_job):
    """
    Fetch all pending jobs created *after* our given render_job.
    It should be safe to mark these all as complete since we are
    going to render the most recently published content.
    """
    meta = get_metadata(render_job)
    baseline = render_job.created
    return [x for x in meta.values()
            if x.is_pending() and x.created >= baseline]


def sync_package_job(render_job, bucket):
    logger.info('Sync content (%s) (%s)',
                render_job.PackageNTIID,
                render_job.job_id)
    job_id = render_job.job_id
    creator = render_job.creator
    endInteraction()
    try:
        # process
        bucket = unpickle(bucket)
        package = get_package(render_job)
        newInteraction(Participation(IPrincipal(creator)))
        copy_and_notify(bucket, package, render_job)
    except Exception as e:
        # XXX: Do we want to fail all applicable jobs?
        logger.exception('Render job %s failed', job_id)
        render_job.update_to_failed_state(str(e))
    else:
        jobs_to_update = get_jobs_to_update(render_job)
        for job in jobs_to_update:
            logger.info('Finished rendering content (%s) (%s)',
                        job.PackageNTIID,
                        job.job_id)
            job.update_to_success_state()
            lifecycleevent.modified(job)
    finally:
        restoreInteraction()
        lifecycleevent.modified(render_job)
