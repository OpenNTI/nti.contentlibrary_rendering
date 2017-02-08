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
from zope import lifecycleevent

from nti.contentlibrary.interfaces import IContentUnit
from nti.contentlibrary.interfaces import IContentPackage
from nti.contentlibrary.interfaces import IContentRendered
from nti.contentlibrary.interfaces import IContentPackageLibrary
from nti.contentlibrary.interfaces import IRenderableContentPackage
from nti.contentlibrary.interfaces import IEclipseContentPackageFactory

from nti.contentlibrary.library import register_content_units
from nti.contentlibrary.library import unregister_content_units

from nti.contentlibrary.zodb import RenderableContentUnit
from nti.contentlibrary.zodb import RenderableContentPackage

from nti.contentlibrary_rendering import RST_MIMETYPE

from nti.contentlibrary_rendering.interfaces import IContentTransformer
from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator

from nti.contentrendering import nti_render

from nti.ntiids.ntiids import find_object_with_ntiid


def copy_attributes(source, target, names):
    for name in names or ():
        value = getattr(source, name, None)
        if value is not None:
            setattr(target, name, value)


def copy_package_data(item, target):
    """
    copy rendered data to target
    """
    factory = IEclipseContentPackageFactory(item)
    package = factory.new_instance(item,
                                   RenderableContentPackage,
                                   RenderableContentUnit)
    assert package is not None, "Invalid rendered content directory"

    # 1. remove package to clear internal structures
    library = component.queryUtility(IContentPackageLibrary)
    if library is not None:
        library.remove(package, event=False, unregister=False)

    # 2. copy all new content package attributes
    copy_attributes(package, target, IContentPackage.names())

    # 3. copy unit attributes
    attributes = set(IContentUnit.names()) - {'children'}
    copy_attributes(package, target, attributes)

    # 4. copy displayable content attributes
    copy_attributes(package, target, ('PlatformPresentationResources',))

    # 5. make sure we copy the new ntiid
    target.ntiid = package.ntiid

    # 6. unregister from the intid facility the target old children
    for unit in target.children or ():
        unregister_content_units(unit)
    
    # 7. register with the intid facility the new children
    target.children = target.children_iterable_factory(package.children or ())
    register_content_units(target, target)

    # 8. [re]register in the library to populate internal structures
    if library is not None:
        library.add(package, event=False)

    return target


def render_latex(tex_source, context=None):
    current_dir = os.getcwd()
    tex_dir = os.path.dirname(tex_source)
    try:
        os.chdir(tex_dir)
        return nti_render.render(tex_source, provider='NTI')
    finally:
        os.chdir(current_dir)


def transform_content(context):
    contentType = context.contentType or RST_MIMETYPE
    transformer = component.getUtility(IContentTransformer,
                                       name=str(contentType))
    return transformer.transform(context.contents, context=context)


def locate_rendered_content(latex_file, context):
    path, name = os.path.split(latex_file)
    name_noe, unused = os.path.splitext(name)
    path = os.path.join(path, name_noe)  # path to rendered contents
    locator = component.getUtility(IRenderedContentLocator)
    return locator.locate(path, context)


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

    # 3. Place in target location
    key_or_bucket = locate_rendered_content(latex_file, package)

    # 4. copy from target
    copy_package_data(key_or_bucket, package)

    # 5. marked as rendered
    interface.alsoProvides(package, IContentRendered)

    # marked changed
    lifecycleevent.modified(package)
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
