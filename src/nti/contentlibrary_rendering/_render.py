#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os

from plasTeX import Base
from plasTeX import TeXDocument

from zope import component
from zope import interface
from zope import lifecycleevent

from zope.annotation.interfaces import IAnnotations

from zope.event import notify as event_notify

from zope.intid.interfaces import IIntIds

from zope.security.interfaces import IPrincipal
from zope.security.interfaces import IParticipation

from zope.security.management import endInteraction
from zope.security.management import newInteraction
from zope.security.management import restoreInteraction

from nti.contentlibrary.interfaces import IContentUnit
from nti.contentlibrary.interfaces import IContentPackage
from nti.contentlibrary.interfaces import IContentRendered
from nti.contentlibrary.interfaces import IContentPackageLibrary
from nti.contentlibrary.interfaces import IRenderableContentPackage
from nti.contentlibrary.interfaces import IEclipseContentPackageFactory

from nti.contentlibrary.interfaces import ContentPackageRenderedEvent
from nti.contentlibrary.interfaces import ContentPackageLocationChanged

from nti.contentlibrary.library import register_content_units
from nti.contentlibrary.library import unregister_content_units

from nti.contentlibrary.utils import get_published_contents
from nti.contentlibrary.utils import get_published_snapshot

from nti.contentlibrary.zodb import RenderableContentUnit
from nti.contentlibrary.zodb import RenderableContentPackage

from nti.contentlibrary_rendering import RST_MIMETYPE

from nti.contentlibrary_rendering.common import mkdtemp

from nti.contentlibrary_rendering.interfaces import IContentTransformer
from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator
from nti.contentlibrary_rendering.interfaces import IPlastexDocumentGenerator
from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.contentrendering import nti_render

from nti.contentrendering.plastexids import patch_all

from nti.contentrendering.render_document import load_packages
from nti.contentrendering.render_document import setup_environ
from nti.contentrendering.render_document import prepare_document_settings

from nti.externalization.oids import to_external_ntiid_oid

from nti.externalization.proxy import removeAllProxies

from nti.ntiids.interfaces import UpdatedNTIIDEvent
from nti.ntiids.interfaces import WillUpdateNTIIDEvent

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


def update_package_ntiid(target, source_package):
    """
    Update our package with the now-rendered ntiid, making sure we copy
    our annotations over (since we store by ntiid).
    """
    old_ntiid = target.ntiid
    event_notify(WillUpdateNTIIDEvent(target, old_ntiid, source_package.ntiid))
    annotes = IAnnotations(target)
    logger.info('Updating ntiid (old=%s) (new=%s)',
                old_ntiid, source_package.ntiid)
    target.ntiid = source_package.ntiid
    _copy_annotations(target, annotes)


def copy_package_data(item, target):
    """
    copy rendered data to target
    """
    factory = IEclipseContentPackageFactory(item)
    package = factory.new_instance(item,
                                   RenderableContentPackage,
                                   RenderableContentUnit)
    assert package is not None, "Invalid rendered content directory"

    # 1. remove target package to clear internal structures
    library = component.queryUtility(IContentPackageLibrary)
    if library is not None:
        library.remove(target, event=False, unregister=False)

    # 2. copy all new content package attributes
    copy_attributes(package, target, IContentPackage.names())

    # 3a. copy unit attributes
    attributes = set(IContentUnit.names()) - {'children', 'ntiid', 'icon'}
    copy_attributes(package, target, attributes)

    # 3b. copy icon
    if not target.icon and package.icon:
        target.icon = package.icon

    # 4. copy displayable content attributes
    copy_attributes(package, target, ('PlatformPresentationResources',))

    # 5. make sure we copy the new ntiid
    old_ntiid = target.ntiid
    if not target.ntiid or is_ntiid_of_type(target.ntiid, TYPE_OID):
        update_package_ntiid(target, package)

    # 6. unregister from the intid facility the target old children
    for unit in target.children or ():
        unregister_content_units(unit)

    # 7. register with the intid facility the new children
    target.children = target.children_iterable_factory(package.children or ())
    register_content_units(target, target)

    # 8. [re]register target package in the library to populate internal
    # structures
    if library is not None:
        library.add(target, event=False)

    # 9. Must broadcast ntiid change event after inserting into library.
    if old_ntiid != target.ntiid:
        event_notify(UpdatedNTIIDEvent(target, old_ntiid, target.ntiid))

    return target


def prepare_tex_document(package=None, provider='NTI', jobname=None,
                         context=None, tex_dom=None, outfile_dir=None):
    """
    Build and prepare context for our plasTeX document, returning
    the new plasTeX document and the jobname.nose2
    """
    # XXX: Do we need to read in render_conf? How about cross-document refs?
    tex_dom = TeXDocument() if tex_dom is None else tex_dom
    Base.document.filenameoverride = property(lambda unused: 'index')
    # Generate a jobname, this is used in the eventual NTIID.
    specific_ntiid = None
    if not jobname:
        if package is not None:
            intids = component.getUtility(IIntIds)
            specific_ntiid = jobname = intids.getId(package)
        else:
            specific_ntiid = jobname = id(tex_dom)
    jobname = str(jobname)
    specific_ntiid = str(specific_ntiid or jobname)
    tex_dom.userdata['jobname'] = jobname
    # Prep our doc
    prepare_document_settings(tex_dom,
                              provider=provider,
                              working_dir=outfile_dir,
                              specific_ntiid=specific_ntiid)
    # Pull in all necessary plugins/configs/templates.
    unused_ctx, packages_path = load_packages(context=context,
                                              load_configs=False)
    setup_environ(tex_dom, jobname, packages_path)
    return tex_dom, jobname


def generate_document(source_doc, tex_dom, content_type=RST_MIMETYPE):
    generator = component.getUtility(IPlastexDocumentGenerator,
                                     name=str(content_type))
    generator.generate(source_doc, tex_dom)
    return tex_dom


def apply_config_overrides(tex_dom):
    # We want a single file, 'index.html'
    tex_dom.config['files']['split-level'] = 0


def render_document(source_doc, package=None, outfile_dir=None,
                    provider='NTI', jobname=None, content_type=RST_MIMETYPE):
    """
    Render the given source document.
    """
    current_dir = os.getcwd()
    outfile_dir = outfile_dir or mkdtemp()
    try:
        os.chdir(outfile_dir)
        # Get a suitable tex dom
        tex_dom, jobname = prepare_tex_document(package,
                                                provider,
                                                jobname=jobname,
                                                outfile_dir=outfile_dir)
        apply_config_overrides(tex_dom)
        # Generate our plasTeX DOM and render.
        generate_document(source_doc, tex_dom, content_type)
        return nti_render.process_document(tex_dom, jobname)
    finally:
        os.chdir(current_dir)


def _get_contents_to_render(package):
    """
    Get the latest published contents for our package, otherwise fall
    back to the current contents on the package.
    """
    contents = get_published_contents(package)
    if contents is None:
        logger.warn('No published contents; falling back to current contents (%s)',
                    package.ntiid)
        contents = package.contents
    return contents


def transform_content(context, contentType, contents=None):
    if contents is None:
        contents = _get_contents_to_render(context)
    transformer = component.getUtility(IContentTransformer,
                                       name=str(contentType))
    return transformer.transform(contents, context=context)


def locate_rendered_content(tex_dom, package):
    # get path to rendered contents
    output_dir = tex_dom.userdata['working-dir']
    path, name = os.path.split(output_dir)
    name_noe, unused = os.path.splitext(name)
    path = os.path.join(path, name_noe)
    # save old location
    old_root = package.root
    # locate
    locator = component.getUtility(IRenderedContentLocator)
    result = locator.locate(path, package)
    # notify location changed
    if old_root is not None:
        event_notify(ContentPackageLocationChanged(package, old_root, result))
    return result


def write_meta_info(package, job, outfile_dir):
    name = os.path.join(outfile_dir, "meta.info")
    with open(name, "wb") as fp:
        fp.write("JobID: %s\n" % job.job_id)
        fp.write("JobCreator: %s\n" % job.creator)
        fp.write("PackageNTIID: %s\n" % package.ntiid)
        fp.write("PackageOID: %s\n" % to_external_ntiid_oid(package))


def process_render_job(render_job):
    ntiid = render_job.PackageNTIID
    provider = render_job.Provider
    package = find_object_with_ntiid(ntiid)
    package = removeAllProxies(package)
    contentType = package.contentType or RST_MIMETYPE
    if package is None:
        raise ValueError("Package not found", ntiid)
    elif not IRenderableContentPackage.providedBy(package):
        raise TypeError("Invalid content package", ntiid)

    current_dir = os.getcwd()
    outfile_dir = mkdtemp()
    try:
        os.chdir(outfile_dir)

        # 1. Transform content into dom
        snapshot = get_published_snapshot(package)
        version = snapshot.version if snapshot else None
        contents = snapshot.contents if snapshot else None
        source_doc = transform_content(package, contentType, contents)
        # save version
        render_job.Version = version 
        
        # 2. Render
        tex_dom = render_document(source_doc,
                                  provider=provider,
                                  package=package,
                                  content_type=contentType,
                                  outfile_dir=outfile_dir)

        # 3. Write meta-info
        write_meta_info(package, render_job, outfile_dir)

        # 4. Place in target location
        key_or_bucket = locate_rendered_content(tex_dom, package)
        render_job.OutputRoot = key_or_bucket  # save

        # 5. copy from target
        copy_package_data(key_or_bucket, package)

        # 6. marked as rendered
        if render_job.MarkRendered:
            interface.alsoProvides(package, IContentRendered)
            event_notify(ContentPackageRenderedEvent(package))

        # marked changed
        lifecycleevent.modified(package)
        return package
    finally:
        os.chdir(current_dir)


@interface.implementer(IParticipation)
class _Participation(object):

    __slots__ = (b'interaction', b'principal')

    def __init__(self, principal):
        self.interaction = None
        self.principal = principal


def _get_metadata(context):
    return IContentPackageRenderMetadata(context, None)


def _get_jobs_to_update(render_job):
    """
    Fetch all pending jobs created *after* our given render_job.
    It should be safe to mark these all as complete since we are
    going to render the most recently published content.
    """
    meta = _get_metadata(render_job)
    baseline = render_job.created
    return (x for x in meta.values()
            if x.is_pending() and x.created >= baseline)


def render_package_job(render_job):
    logger.info('Rendering content (%s) (%s)',
                render_job.PackageNTIID,
                render_job.job_id)
    job_id = render_job.job_id
    creator = render_job.creator
    output_root = render_job.OutputRoot
    endInteraction()
    try:
        newInteraction(_Participation(IPrincipal(creator)))
        if output_root is None:
            process_render_job(render_job)
        else:
            logger.warn("Processing already completed for job %s", 
                        render_job.job_id)
    except Exception as e:
        # XXX: Do we want to fail all applicable jobs?
        logger.exception('Render job %s failed', job_id)
        render_job.update_to_failed_state(str(e))
    else:
        jobs_to_update = _get_jobs_to_update(render_job)
        for job in jobs_to_update:
            logger.info('Finished rendering content (%s) (%s)',
                        job.PackageNTIID,
                        job.job_id)
            job.update_to_success_state()
            lifecycleevent.modified(job)
    finally:
        restoreInteraction()
        lifecycleevent.modified(render_job)
        lifecycleevent.modified(_get_metadata(render_job))
