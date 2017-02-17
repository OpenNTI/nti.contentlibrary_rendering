#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import tempfile

from plasTeX import Base
from plasTeX import TeXDocument

from zope import component
from zope import interface
from zope import lifecycleevent

from zope.intid.interfaces import IIntIds

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
from nti.contentlibrary_rendering.interfaces import IPlastexDocumentGenerator

from nti.contentrendering import nti_render

from nti.contentrendering.plastexids import patch_all

from nti.contentrendering.render_document import load_packages
from nti.contentrendering.render_document import setup_environ
from nti.contentrendering.render_document import prepare_document_settings

from nti.externalization.proxy import removeAllProxies

from nti.ntiids.ntiids import TYPE_OID
from nti.ntiids.ntiids import is_ntiid_of_type
from nti.ntiids.ntiids import find_object_with_ntiid

# Patch our plastex early.
patch_all()


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
    attributes = set(IContentUnit.names()) - {'children', 'ntiid'}
    copy_attributes(package, target, attributes)

    # 4. copy displayable content attributes
    copy_attributes(package, target, ('PlatformPresentationResources',))

    # 5. make sure we copy the new ntiid
    if not target.ntiid or is_ntiid_of_type(target.ntiid, TYPE_OID):
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


def _get_and_prepare_doc(context, provider='NTI', jobname=None):
    """
    Build and prepare context for our plasTeX document.
    """
    # XXX: Do we need to read in render_conf? How about cross-document refs?
    tex_dom = TeXDocument()
    Base.document.filenameoverride = property(lambda unused: 'index')
    # Prep our doc
    prepare_document_settings(tex_dom, provider=provider)
    # Pull in all necessary plugins/configs/templates.
    unused_ctx, packages_path = load_packages(context=context,
                                              load_configs=False)
    setup_environ(tex_dom, jobname, packages_path)
    if jobname is None:
        intids = component.getUtility(IIntIds)
        jobname = intids.getId(context)
    tex_dom.userdata['jobname'] = jobname
    return tex_dom


def render_document(source_doc, context=None, outfile_dir=None,
                    provider='NTI', jobname=None, content_type=RST_MIMETYPE):
    """
    Render the given source document.
    """
    # XXX: do we need to patch_all here?
    current_dir = os.getcwd()
    tex_dir = outfile_dir or tempfile.mkdtemp()
    try:
        os.chdir(tex_dir)
        tex_dom = _get_and_prepare_doc(context, provider, jobname)
        # Generate our plasTeX DOM and render.
        generator = component.getUtility(IPlastexDocumentGenerator,
                                         name=str(content_type))
        generator.generate(source_doc, tex_dom)
        return nti_render.process_document(tex_dom, jobname)
    finally:
        os.chdir(current_dir)


def transform_content(context, contentType):
    transformer = component.getUtility(IContentTransformer,
                                       name=str(contentType))
    return transformer.transform(context.contents, context=context)


def locate_rendered_content(tex_dom, context):
    output_dir = tex_dom.userdata['working-dir']
    path, name = os.path.split(output_dir)
    name_noe, unused = os.path.splitext(name)
    path = os.path.join(path, name_noe)  # path to rendered contents
    locator = component.getUtility(IRenderedContentLocator)
    return locator.locate(path, context)


def _do_render_package(render_job):
    ntiid = render_job.PackageNTIID
    provider = render_job.Provider
    package = find_object_with_ntiid(ntiid)
    package = removeAllProxies(package)
    contentType = package.contentType or RST_MIMETYPE
    if package is None:
        raise ValueError("Package not found", ntiid)
    elif not IRenderableContentPackage.providedBy(package):
        raise TypeError("Invalid content package", ntiid)

    # 1. Transform content into dom
    source_doc = transform_content(package, contentType)

    # 2. Render
    tex_dom = render_document(source_doc,
                              provider=provider,
                              context=package,
                              content_type=contentType)

    # 3. Place in target location
    key_or_bucket = locate_rendered_content(tex_dom, package)

    # 4. copy from target
    copy_package_data(key_or_bucket, package)

    # 5. marked as rendered
    if render_job.MarkRendered:
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
