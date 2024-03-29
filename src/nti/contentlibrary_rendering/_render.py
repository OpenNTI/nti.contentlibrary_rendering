#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import time
import importlib

from plasTeX import Base
from plasTeX import TeXDocument

from zope import component
from zope import interface
from zope import lifecycleevent

from zope.annotation.interfaces import IAnnotations

from zope.event import notify as event_notify

from zope.intid.interfaces import IIntIds

from z3c.autoinclude.plugin import find_plugins

from nti.base._compat import text_

from nti.contentlibrary import RST_MIMETYPE

from nti.contentlibrary.interfaces import IContentUnit
from nti.contentlibrary.interfaces import IContentPackage
from nti.contentlibrary.interfaces import IContentRendered
from nti.contentlibrary.interfaces import IContentPackageLibrary
from nti.contentlibrary.interfaces import ContentUnitRemovedEvent
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

from nti.contentlibrary_rendering import NTI_PROVIDER
from nti.contentlibrary_rendering import CONTENT_UNITS_HSET
from nti.contentlibrary_rendering import CONTENT_UNITS_HSET_EXPIRY

from nti.contentlibrary_rendering.common import dump
from nti.contentlibrary_rendering.common import mkdtemp
from nti.contentlibrary_rendering.common import unpickle
from nti.contentlibrary_rendering.common import redis_client

from nti.contentlibrary_rendering.interfaces import IContentTransformer
from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator
from nti.contentlibrary_rendering.interfaces import IPlastexDocumentGenerator
from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.contentrendering import nti_render

from nti.contentrendering.plastexids import patch_all

from nti.contentrendering.render_document import PP_CONTENT_RENDERING

from nti.contentrendering.render_document import load_packages
from nti.contentrendering.render_document import setup_environ
from nti.contentrendering.render_document import prepare_document_settings

from nti.externalization.proxy import removeAllProxies

from nti.ntiids.ntiids import find_object_with_ntiid

logger = __import__('logging').getLogger(__name__)


# Patch our plastex early.
patch_all()


# metadata


class Metadata(object):
    icon = None
    title = None
    description = None
    key_or_bucket = None


def create_metadata(tex_dom, key_or_bucket=None):
    result = Metadata()
    result.key_or_bucket = key_or_bucket
    result.icon = tex_dom.userdata.get('icon')
    result.title = tex_dom.userdata.get('title')
    result.description = tex_dom.userdata.get('description')
    return result


def save_metadata(job_id, item, expiry=CONTENT_UNITS_HSET_EXPIRY):
    try:
        redis = redis_client()
        if redis is not None:
            data = dump(item)
            pipe = redis.pipeline()
            pipe.hset(CONTENT_UNITS_HSET, job_id, data).expire(job_id, expiry)
            pipe.execute()
            return True
    except Exception:  # pylint: disable=broad-except
        logger.exception("Could not place %s in %s for %s",
                         item, CONTENT_UNITS_HSET, job_id)
    return False
save_delimited_item = save_metadata  # BWC


def get_metadata(job_id):
    try:
        redis = redis_client()
        if redis is not None:
            data = redis.hget(CONTENT_UNITS_HSET, job_id)
            if data is not None:
                return unpickle(data)
    except Exception:  # pylint: disable=broad-except
        logger.exception("Could not get metadata from %s for %s",
                         CONTENT_UNITS_HSET, job_id)
    return None
get_delimited_item = get_metadata  # BWC


def delete_metadata(job_id):
    try:
        redis = redis_client()
        if redis is not None:
            redis.hdel(CONTENT_UNITS_HSET, job_id)
    except Exception:  # pylint: disable=broad-except
        logger.exception("Could not delete metadata from %s for %s",
                         CONTENT_UNITS_HSET, job_id)
    return None
delete_delimited_item = delete_metadata  # BWC


# rendering


def is_default_icon(icon=None, package=None):
    title = getattr(package, 'title', None) or ''
    icon = getattr(icon, 'absolute_path', None) \
        or getattr(icon, 'name', None) or icon
    return not icon \
        or icon.endswith('icons/chapters/generic_book.png') \
        or icon.endswith('images/backgrounds/default.png') \
        or icon.endswith('images/backgrounds/default.jpg') \
        or icon.endswith("icons/chapters/" + title + "-icon.png")


def copy_attributes(source, target, names):
    for name in names or ():
        value = getattr(source, name, None)
        if value is not None:
            setattr(target, name, value)


def copy_annotations(package, old_annotations):
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
    # pylint: disable=too-many-function-args
    # pylint: disable=no-value-for-parameter
    factory = IEclipseContentPackageFactory(item)
    package = factory.new_instance(item,
                                   RenderableContentPackage,
                                   RenderableContentUnit)
    assert package is not None, "Invalid rendered content directory"

    # 1. remove target package to clear internal structures
    library = component.queryUtility(IContentPackageLibrary)
    if library is not None:  # tests
        library.remove(target, event=False, unregister=False)

    # 2. copy all new content package attributes
    copy_attributes(package, target, IContentPackage.names())

    # 3. copy unit attributes
    attributes = set(IContentUnit.names()) - {'children', 'ntiid', 'icon'}
    copy_attributes(package, target, attributes)

    # 4. copy icon
    if is_default_icon(target.icon) and package.icon:
        target.icon = package.icon

    # 5. copy displayable content attributes
    copy_attributes(package, target, ('PlatformPresentationResources',))

    # 6. unregister from the intid facility the target old children
    old_children = list(target.children or ())
    for unit in old_children:
        unregister_content_units(unit)

    # 7. register with the intid facility the new children
    target.children = target.children_iterable_factory(package.children or ())
    register_content_units(target, target)

    # 8. Broadcast unit removal
    new_children_ntiids = set(x.ntiid for x in target.children)
    for child in old_children:
        if child.ntiid not in new_children_ntiids:
            event_notify(ContentUnitRemovedEvent(child))

    # 9. register target package in the library to populate internal
    # structures
    if library is not None:  # tests
        library.add(target, event=False)
    return target


def prepare_environment(tex_dom, jobname, packages_path):
    xhtmltemplates = []
    for plugin in find_plugins(PP_CONTENT_RENDERING.__name__):
        name = plugin.project_name.replace('-', '_')
        if name == PP_CONTENT_RENDERING.__name__:
            continue
        module = importlib.import_module(name)
        location = module.__path__[0]
        for postfix in ('', 'plastexpackages', 'zpts'):
            path = os.path.join(location, postfix)
            if os.path.exists(path):
                xhtmltemplates.append(path)
    os.environ['XHTMLTEMPLATES'] = os.path.pathsep.join(xhtmltemplates)
    setup_environ(tex_dom, jobname, packages_path)


def prepare_tex_document(package=None, provider=NTI_PROVIDER, jobname=None,
                         context=None, tex_dom=None, outfile_dir=None):
    """
    Build and prepare context for our plasTeX document, returning
    the new plasTeX document and the jobname.nose2
    """
    # Do we need to read in render_conf? How about cross-document refs?
    tex_dom = TeXDocument() if tex_dom is None else tex_dom
    Base.document.filenameoverride = property(lambda unused: 'index')
    # Generate a jobname, this is used in the eventual NTIID.
    specific_ntiid = None
    if not jobname:
        if package is not None:
            intids = component.getUtility(IIntIds)
            specific_ntiid = jobname = intids.getId(package)
            tex_dom.userdata['document_ntiid'] = package.ntiid
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
    context, packages_path = load_packages(context=context,
                                           load_configs=False)
    prepare_environment(tex_dom, jobname, packages_path)
    return tex_dom, jobname


def generate_document(source_doc, tex_dom, content_type=RST_MIMETYPE, context=None):
    generator = component.getUtility(IPlastexDocumentGenerator,
                                     name=str(content_type))
    generator.generate(source_doc, tex_dom, context)
    return tex_dom


def apply_config_overrides(tex_dom):
    # We want a single file, 'index.html'
    tex_dom.config['files']['split-level'] = 0


def render_document(source_doc, package=None, outfile_dir=None,
                    provider=NTI_PROVIDER, jobname=None, content_type=RST_MIMETYPE):
    """
    Render the given source document.
    """
    current_dir = os.getcwd()
    outfile_dir = outfile_dir or mkdtemp()
    xhtmltemplates = os.environ.get('XHTMLTEMPLATES', '')
    try:
        os.chdir(outfile_dir)
        # make sure chameleon cache
        cache_dir = os.environ.get('CHAMELEON_CACHE', None)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        # Get a suitable tex dom
        tex_dom, jobname = prepare_tex_document(package,
                                                provider,
                                                jobname=jobname,
                                                outfile_dir=outfile_dir)
        apply_config_overrides(tex_dom)
        # Generate our plasTeX DOM and render.
        generate_document(source_doc, tex_dom, content_type, package)
        return nti_render.process_document(tex_dom, jobname, docachefile=False)
    finally:
        os.chdir(current_dir)
        os.environ['XHTMLTEMPLATES'] = xhtmltemplates


def get_contents_to_render(package):
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
        contents = get_contents_to_render(context)
    transformer = component.getUtility(IContentTransformer,
                                       name=str(contentType))
    return transformer.transform(contents, context)


def content_package_pocation_changed(package, old, new):
    if old is not None:
        event_notify(ContentPackageLocationChanged(package, old, new))


def locate_rendered_content(tex_dom, package):
    # get path to rendered contents
    output_dir = tex_dom.userdata['working-dir']
    path, name = os.path.split(output_dir)
    name_noe, unused_ext = os.path.splitext(name)
    path = os.path.join(path, name_noe)
    # save old location
    old_root = getattr(package, 'root', None) \
            or getattr(package, 'key', None)
    # locate
    locator = component.getUtility(IRenderedContentLocator)
    result = locator.locate(path, package)
    # notify location changed
    content_package_pocation_changed(package, old_root, result)
    return result


def copy_and_notify(bucket, package, render_job, metadata=None):
    # 4. copy from target
    copy_package_data(bucket, package)

    # 5. copy from metadata
    if metadata is not None and metadata.icon:
        package.icon = metadata.icon

    # 6. marked as rendered
    if render_job.MarkRendered:
        interface.alsoProvides(package, IContentRendered)
        event_notify(ContentPackageRenderedEvent(package))

    # marked changed
    lifecycleevent.modified(package)
    return package


def get_package(render_job):
    ntiid = render_job.PackageNTIID
    package = find_object_with_ntiid(ntiid)
    package = removeAllProxies(package)
    if package is None:
        raise ValueError("Package not found", ntiid)
    elif not IRenderableContentPackage.providedBy(package):
        raise TypeError("Invalid content package", ntiid)
    return package


def process_render_job(render_job):
    provider = render_job.Provider
    package = get_package(render_job)
    contentType = package.contentType or RST_MIMETYPE

    current_dir = os.getcwd()
    outfile_dir = mkdtemp()
    try:
        os.chdir(outfile_dir)
        # 1. Transform content into dom
        snapshot = get_published_snapshot(package)
        version = snapshot.version if snapshot else None
        contents = snapshot.contents if snapshot else None
        source_doc = transform_content(package, contentType, contents)
        # 1a. version
        render_job.Version = version
        # 2. Render
        tex_dom = render_document(source_doc,
                                  provider=provider,
                                  package=package,
                                  content_type=contentType,
                                  outfile_dir=outfile_dir)
        # 3. Place in target location
        key_or_bucket = locate_rendered_content(tex_dom, package)
        render_job.OutputRoot = key_or_bucket  # save
        # 3a. save metadata in redis in case a retry
        metadata = create_metadata(tex_dom, key_or_bucket)
        save_metadata(render_job.job_id, metadata)
        # copy rendered data and notify
        copy_and_notify(key_or_bucket, package, render_job, metadata)
        return package
    finally:
        os.chdir(current_dir)


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
    return [
        x for x in meta.values() if x.is_pending() and x.created >= baseline
    ]


def render_package_job(render_job):
    start_time = time.time()
    logger.info('Rendering content (%s) (%s)',
                render_job.PackageNTIID,
                render_job.job_id)
    job_id = render_job.job_id
    try:
        metadata = get_metadata(job_id)
        key_or_bucket = metadata.key_or_bucket if metadata else None
        if key_or_bucket is None or not key_or_bucket.exists():
            process_render_job(render_job)
        else:
            # if the transaction has aborted don't render
            # simply copy the contents again from previous
            # render operation
            package = get_package(render_job)
            logger.warning("Due to a transaction abort, copying data from %s for package %s",
                           key_or_bucket, package.ntiid)
            old_root = package.root
            copy_and_notify(key_or_bucket, package, render_job, metadata)
            render_job.OutputRoot = key_or_bucket  # save
            content_package_pocation_changed(package, old_root, key_or_bucket)
    except Exception as e:  # pylint: disable=broad-except
        # Do we want to fail all applicable jobs?
        logger.exception('Render job %s failed', job_id)
        render_job.update_to_failed_state(text_(str(e)))
    else:
        duration = time.time() - start_time
        jobs_to_update = _get_jobs_to_update(render_job)
        for job in jobs_to_update:
            logger.info('Finished rendering content (%s) (%s) (%.2fs)',
                        job.PackageNTIID,
                        job.job_id,
                        duration)
            job.update_to_success_state()
            lifecycleevent.modified(job)
    finally:
        lifecycleevent.modified(render_job)
