#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import bz2
import sys
import gzip
import time
import shutil
import zipfile
import tarfile
import tempfile
import traceback
import simplejson

import transaction

from zope import component
from zope import lifecycleevent

from zope.security.interfaces import IPrincipal

from zope.security.management import endInteraction
from zope.security.management import newInteraction
from zope.security.management import restoreInteraction

from nti.contentlibrary.filesystem import FilesystemBucket

from nti.contentlibrary.interfaces import IContentPackageLibrary
from nti.contentlibrary.interfaces import IEclipseContentPackageFactory

from nti.contentlibrary.utils import get_content_package_site

from nti.contentlibrary_rendering import CONTENT_UNITS_HSET
from nti.contentlibrary_rendering import LIBRARY_RENDER_JOB
from nti.contentlibrary_rendering import CONTENT_UNITS_QUEUE

from nti.contentlibrary_rendering.common import dump
from nti.contentlibrary_rendering.common import unpickle
from nti.contentlibrary_rendering.common import get_site
from nti.contentlibrary_rendering.common import get_creator
from nti.contentlibrary_rendering.common import redis_client
from nti.contentlibrary_rendering.common import Participation

from nti.contentlibrary_rendering.interfaces import FAILED
from nti.contentlibrary_rendering.interfaces import PENDING
from nti.contentlibrary_rendering.interfaces import RUNNING
from nti.contentlibrary_rendering.interfaces import SUCCESS
from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator

from nti.contentlibrary_rendering.model import LibraryRenderJob

from nti.contentlibrary_rendering.processing import put_generic_job

from nti.contentrendering.nti_render import render as nti_render

from nti.contentrendering.plastexids import patch_all

from nti.coremetadata.interfaces import SYSTEM_USER_ID

from nti.zodb.containers import time_to_64bit_int

from nti.ntiids.ntiids import make_ntiid
from nti.ntiids.ntiids import make_specific_safe


# Patch our plastex early.
patch_all()

# common

EXPIRY_TIME = 86400  # 24hrs


def format_exception(e):
    result = []
    exc_type, exc_value, exc_traceback = sys.exc_info()
    result['message'] = str(e)
    result['code'] = e.__class__.__name__
    result['traceback'] = repr(traceback.format_exception(exc_type,
                                                          exc_value,
                                                          exc_traceback))
    return simplejson.dumps(result, indent='\t')


# jobs


def generate_job_id(source, creator=None):
    creator = get_creator(creator) or SYSTEM_USER_ID
    current_time = time_to_64bit_int(time.time())
    specific = "%s_%s_%s" % (creator, source.filename, current_time)
    specific = make_specific_safe(specific)
    return make_ntiid(nttype=LIBRARY_RENDER_JOB, specific=specific)


def job_id_status(job_id):
    return "%s=status" % job_id


def job_id_error(job_id):
    return "%s=error" % job_id


def get_job_status(job_id):
    redis = redis_client()
    if redis is not None:
        key = job_id_status(job_id)
        return redis.get(key)


def get_job_error(job_id):
    redis = redis_client()
    if redis is not None:
        key = job_id_error(job_id)
        return redis.get(key)


def update_job_status(job_id, status, expiry=EXPIRY_TIME):
    redis = redis_client()
    if redis is not None:
        key = job_id_status(job_id)
        redis.setex(key, value=status, time=expiry)
        return key


def update_job_error(job_id, error, expiry=EXPIRY_TIME):
    redis = redis_client()
    if redis is not None:
        key = job_id_error(job_id)
        redis.setex(key, value=error, time=expiry)
        return key


def create_render_job(source, creator, provider='NTI'):
    result = LibraryRenderJob()
    result.job_id = generate_job_id(source, creator)
    result.source = source
    result.creator = creator
    result.provider = provider
    return result


def store_job(job, expiry=EXPIRY_TIME):
    redis = redis_client()
    redis.setex(job.job_id, value=dump(job), time=expiry)
    return job


def load_job(job_id):
    redis = redis_client()
    pipe = redis.pipeline()
    result = pipe.get(job_id).delete(job_id).execute()
    job = result[0] if result else None
    job = unpickle(job) if job is not None else None
    return job


def save_delimited_item(job_id, item, expiry=EXPIRY_TIME):
    redis = redis_client()
    if redis is not None:
        pipe = redis.pipeline()
        pipe.hset(CONTENT_UNITS_HSET, job_id, item).expire(job_id, expiry)
        pipe.execute()
        return True
    return False


def get_delimited_item(job_id):
    redis = redis_client()
    if redis is not None:
        return redis.hget(CONTENT_UNITS_HSET, job_id)
    return None


# source


def is_archive(source, magic):
    if hasattr(source, "read"):
        source.seek(0)
        file_start = source.read(len(magic))
    else:
        with open(source, "rb") as fp:
            file_start = fp.read(len(magic))
    return file_start.startswith(magic)


def is_gzip(source):
    return is_archive(source, b"\x1f\x8b\x08")


def is_bz2(source):
    return is_archive(source, b"\x42\x5a\x68")


def process_source(source):
    if not os.path.isfile(source):
        return source
    if is_gzip(source):
        target, _ = os.path.splitext(source)
        with gzip.open(source, "rb") as f_in, open(target, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        return process_source(target)
    elif is_bz2(source):
        target, _ = os.path.splitext(source)
        with bz2.BZ2File(source) as f_in, open(target, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        return process_source(target)
    elif tarfile.is_tarfile(source):
        target = tempfile.mkdtemp()
        tar = tarfile.TarFile(source)
        tar.extractall(target)
        files = os.listdir(target)
        if files and len(files) == 1 and os.path.isdir(files[0]):
            target = os.path.join(target, files[0])
        return process_source(target)
    elif zipfile.is_zipfile(source):
        target = tempfile.mkdtemp()
        zf = zipfile.ZipFile(source)
        zf.extractall(target)
        files = os.listdir(target)
        if files and len(files) == 1 and os.path.isdir(files[0]):
            target = os.path.join(target, files[0])
        return process_source(target)
    else:
        return source  # assume renderable


def save_source(source, path=None):
    path = path or tempfile.mkdtemp()
    name = os.path.split(source.filename)[1]
    name = os.path.join(path, name)
    with open(name, "wb") as fp:
        fp.write(source.data)
    return name


# content pacakges


def content_package_library():
    return component.queryUtility(IContentPackageLibrary)


def get_rendered_package(path):
    name = os.path.split(path)[1]
    bucket = FilesystemBucket(name=name)
    bucket.absolute_path = path  # local path
    factory = IEclipseContentPackageFactory(bucket)
    package = factory.new_instance(bucket)
    assert package is not None, "Invalid rendered content directory"
    return package


def move_content(library, path):
    enumeration = library.enumeration
    root = getattr(enumeration, 'root', None) \
        or getattr(enumeration, 'bucket', None)
    locator = component.getUtility(IRenderedContentLocator)
    locator.move(path, root)


def update_library(ntiid, path, retry=False):
    library = content_package_library()
    if library is None:  # tests
        return
    if not retry:  # trx retry
        move_content(library, path)
    package = library.get(ntiid)
    is_new = (package is None or
              get_content_package_site(package) != get_site())
    # enumerate all content packages to build new pkgs
    enumeration = library.enumeration
    content_packages = enumeration.enumerateContentPackages()
    content_packages = {x.ntiid: x for x in content_packages}
    assert ntiid in content_packages
    # replace or add
    updated = content_packages[ntiid]
    if not is_new:
        library.replace(updated)
    else:
        library.add(updated)
    return updated


# rendering


def find_renderable(archive):
    if os.path.isfile(archive):
        return archive  # assume renderable
    tex = os.path.basename(archive) + '.tex'
    if os.path.exists(os.path.join(archive, tex)):
        return os.path.join(archive, tex)
    for name in os.listdir(archive):
        lname = name.lower()
        if lname.endswith('.tex'):
            return os.path.join(archive, name)
    raise ValueError("Cannot find renderable LaTeX file")


def render_source(source, provider='NTI', docachefile=False):
    source = os.path.abspath(source)
    archive = process_source(source)
    tex_file = find_renderable(archive)
    path, _ = os.path.split(tex_file)
    current_dir = os.getcwd()
    try:
        os.chdir(path)
        nti_render(tex_file,
                   provider,
                   load_configs=False,
                   docachefile=docachefile,
                   set_chameleon_cache=False)
    finally:
        os.chdir(current_dir)
    return tex_file


def render_library_job(render_job):
    logger.info('Rendering content (%s)', render_job.job_id)
    job_id = render_job.job_id
    creator = render_job.creator
    endInteraction()
    try:
        retry = False
        update_job_status(job_id, RUNNING)
        tex_file = get_delimited_item(job_id)
        if tex_file is None:
            tmp_dir = tempfile.mkdtemp()
            newInteraction(Participation(IPrincipal(creator)))
            # 1. save source to a local path
            source = save_source(render_job.source, tmp_dir)
            # 2. render contents
            tex_file = render_source(source, render_job.Provider)
            # 3. save in case of a retry
            save_delimited_item(job_id, tex_file)
        else:
            retry = True
            logger.warn("Due to a transaction abort, using data from %s for job %s",
                        tex_file, job_id)
        # 4. Get package info
        out_path = os.path.splitext(tex_file)[0]
        package = get_rendered_package(out_path)
        # 5. Update library
        update_library(package.ntiid, out_path, retry)
        # 6. clean on commit

        def after_commit_or_abort(success=False):
            if success:
                update_job_status(job_id, SUCCESS)
                shutil.rmtree(tmp_dir, ignore_errors=True)
        transaction.get().addAfterCommitHook(after_commit_or_abort)
    except Exception as e:
        logger.exception('Render job %s failed', job_id)
        traceback_msg = format_exception(e)
        render_job.update_to_failed_state(traceback_msg)
        update_job_status(job_id, FAILED)
        update_job_error(job_id, traceback_msg)
    else:
        logger.info('Render (%s) completed', job_id)
        render_job.update_to_success_state()
        lifecycleevent.modified(render_job)
    finally:
        restoreInteraction()
        lifecycleevent.modified(render_job)
    return render_job


def render_job(job_id):
    job = load_job(job_id)
    if job is None:
        update_job_status(job_id, FAILED)
        update_job_error(job_id,
                         simplejson.dumps("Job is missing"))
        logger.error("Job %s is missing", job_id)
    else:
        render_library_job(job)


def render_archive(source, creator, provider='NTI', site=None):
    site_name = get_site(site)
    # 1. create job
    job = create_render_job(source, get_creator(creator), provider)
    # 2. store job
    store_job(job)
    # 3. update status
    update_job_status(job.job_id, PENDING)
    # 4. queue job
    put_generic_job(CONTENT_UNITS_QUEUE,
                    render_job,
                    job_id=job.job_id,
                    site_name=site_name)
    return job
