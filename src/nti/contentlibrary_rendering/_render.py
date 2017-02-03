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
from zope import interface

from nti.contentlibrary.filesystem import FilesystemBucket
from nti.contentlibrary.filesystem import PersistentFilesystemContentUnit
from nti.contentlibrary.filesystem import PersistentFilesystemContentPackage

from nti.contentlibrary.filesystem import package_factory

from nti.contentlibrary.interfaces import IContentPackage
from nti.contentlibrary.interfaces import IContentRendered
from nti.contentlibrary.interfaces import IRenderableContentPackage

from nti.contentlibrary_rendering import RST_MIMETYPE

from nti.contentlibrary_rendering.interfaces import IContentTransformer

from nti.contentrendering import nti_render

from nti.ntiids.ntiids import find_object_with_ntiid


def copy_attributes(source, target, names):
    for name in names or ():
        value = getattr(source, name, None)
        if value is not None:
            setattr(target, name, value)


def copy_package_data(path, target):
    """
    copy rendered data to target
    """
    bucket = FilesystemBucket(name="contents")
    bucket.absolute_path = path
    package = package_factory(bucket,
                              PersistentFilesystemContentPackage,
                              PersistentFilesystemContentUnit)
    assert package is not None, "Invalid rendered content directory"

    # all content pacakge attributes
    copy_attributes(package, target, IContentPackage.names())

    # content unit attributes
    copy_attributes(package, target, ('icon', 'thumbnail', 'href', 'key'))

    # displayable content
    copy_attributes(package, target, ('PlatformPresentationResources',))


def render_latex(tex_source, unit=None):
    return nti_render.render(tex_source)


def transform_content(context):
    contentType = context.contentType or RST_MIMETYPE
    transformer = component.getUtility(IContentTransformer,
                                       name=str(contentType))
    return transformer.transform(context.contents, context=context)


def _do_render_package(render_job):
    ntiid = render_job.PackageNTIID
    package = find_object_with_ntiid(ntiid)
    if package is None:
        raise ValueError("Package not found", ntiid)
    elif not IRenderableContentPackage.providedBy(package):
        raise TypeError("Invalid content package", ntiid)
    # 1. Transform to latex
    latex_file = transform_content(package)
    # 2. Render
    render_latex(latex_file, package)
    # 3. TODO: Place in target location
    # 4. copy from target
    path, name = os.path.split(latex_file)
    name_noe, unused = os.path.splitext(name)
    path = os.path.join(path, name_noe)  # path to rendered contents
    copy_package_data(path, package)
    # 5. marked as rendered
    interface.alsoProvides(package, IContentRendered)
    return package


def render_package_job(render_job):
    logger.info('Rendering content (%s) (%s)',
                render_job.PackageNTIID,
                render_job.job_id)
    job_id = render_job.job_id
    try:
        _do_render_package(render_job)
    except Exception as e:
        logger.exception('Render job %s failed', job_id)
        render_job.update_to_failed_state(str(e))
    else:
        logger.info('Finished rendering content (%s) (%s)',
                    render_job.PackageNTIID,
                    render_job.job_id)
        render_job.update_to_success_state()
