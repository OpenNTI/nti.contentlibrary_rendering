#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import six
import sys
import time
import shutil
import socket
import tempfile
import importlib
from six.moves import configparser

import simplejson

import transaction

from lxml import etree

from zope import component
from zope import exceptions
from zope import lifecycleevent

from z3c.autoinclude.plugin import find_plugins

from nti.base._compat import text_

from nti.common.io import extract_all as process_source

from nti.contentlibrary import RENDERED_PREFIX

from nti.contentlibrary.interfaces import IContentPackageLibrary

from nti.contentlibrary.utils import get_content_package_site

from nti.contentlibrary_rendering import NTI_PROVIDER
from nti.contentlibrary_rendering import CONTENT_UNITS_HSET
from nti.contentlibrary_rendering import LIBRARY_RENDER_JOB
from nti.contentlibrary_rendering import CONTENT_UNITS_QUEUE

from nti.contentlibrary_rendering.common import dump
from nti.contentlibrary_rendering.common import unpickle
from nti.contentlibrary_rendering.common import get_site
from nti.contentlibrary_rendering.common import get_creator
from nti.contentlibrary_rendering.common import redis_client
from nti.contentlibrary_rendering.common import sha1_hex_digest

from nti.contentlibrary_rendering.interfaces import FAILED
from nti.contentlibrary_rendering.interfaces import PENDING
from nti.contentlibrary_rendering.interfaces import RUNNING
from nti.contentlibrary_rendering.interfaces import SUCCESS
from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator

from nti.contentlibrary_rendering.model import LibraryRenderJob

from nti.contentlibrary_rendering.processing import put_generic_job

from nti.contentrendering.nti_render import render as nti_render

from nti.contentrendering.plastexids import patch_all

from nti.contentrendering.render_document import PP_CONTENT_RENDERING

from nti.coremetadata.interfaces import SYSTEM_USER_ID

from nti.namedfile.file import safe_filename

from nti.ntiids.ntiids import make_ntiid
from nti.ntiids.ntiids import make_specific_safe

from nti.zodb.containers import time_to_64bit_int

# common

EXPIRY_TIME = 172800  # 48hrs

logger = __import__('logging').getLogger(__name__)


# Patch our plastex early.
patch_all()


def prepare_json_text(s):
    result = s.decode('utf-8') if isinstance(s, bytes) else s
    return result


def format_exception(e):
    result = dict()
    exc_type, exc_value, exc_traceback = sys.exc_info()
    result['message'] = str(e)
    result['code'] = e.__class__.__name__
    result['traceback'] = repr(exceptions.format_exception(exc_type,
                                                           exc_value,
                                                           exc_traceback,
                                                           with_filenames=True))
    del exc_traceback
    return simplejson.dumps(result, indent='\t')


# jobs


def generate_job_id(source, creator=None):
    creator = get_creator(creator) or SYSTEM_USER_ID
    current_time = time_to_64bit_int(time.time())
    specific = u"%s_%s_%s" % (creator, source.filename, current_time)
    specific = make_specific_safe(specific)
    return make_ntiid(nttype=LIBRARY_RENDER_JOB, specific=specific)


def job_id_status(job_id):
    return "%s=status" % job_id


def job_id_error(job_id):
    return "%s=error" % job_id


def job_id_package_ntiid(job_id):
    return "%s=package_ntiid" % job_id


def get_job_status(job_id):
    redis = redis_client()
    if redis is not None:
        key = job_id_status(job_id)
        return redis.get(key)


def get_job_package_ntiid(job_id):
    redis = redis_client()
    if redis is not None:
        key = job_id_package_ntiid(job_id)
        return redis.get(key)


def get_job_error(job_id):
    redis = redis_client()
    if redis is None:
        return None
    key = job_id_error(job_id)
    result = redis.get(key)
    result = simplejson.loads(prepare_json_text(result)) if result else None
    if isinstance(result, six.string_types):
        result = {
            'message': result,
            'code': 'AssertionError'
        }
    return result


def update_job_status(job_id, status, expiry=EXPIRY_TIME):
    redis = redis_client()
    if redis is not None:
        key = job_id_status(job_id)
        redis.setex(key, time=expiry, value=status)
        return key


def update_job_error(job_id, error, expiry=EXPIRY_TIME):
    redis = redis_client()
    if redis is not None:
        key = job_id_error(job_id)
        redis.setex(key, time=expiry, value=error)
        return key


def update_job_package_ntiid(job_id, ntiid, expiry=EXPIRY_TIME):
    redis = redis_client()
    if redis is not None:
        key = job_id_package_ntiid(job_id)
        redis.setex(key, time=expiry, value=ntiid)
        return key


def create_render_job(source, creator, provider=NTI_PROVIDER):
    result = LibraryRenderJob()
    result.job_id = generate_job_id(source, creator)
    result.source = source
    result.creator = creator
    result.provider = provider
    return result


def store_job(job, expiry=EXPIRY_TIME):
    redis = redis_client()
    redis.setex(job.job_id, time=expiry, value=dump(job))
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


def hex_name(name, now=None, bound=20):
    now = now or time.time()
    digest = sha1_hex_digest(six.binary_type(name),
                             six.binary_type(now),
                             six.binary_type(socket.gethostname()))
    return digest[bound:].upper()  # 40 char string


def obfuscate_filename(name, bound=15):
    hostname = socket.gethostname()
    name = "%s_%s_%s.%s" % (RENDERED_PREFIX, hostname,
                            name[:bound], hex_name(name))
    name = safe_filename(name)
    return name


def save_source(source, path=None):
    path = path or tempfile.mkdtemp()
    name = os.path.split(source.filename)[1]
    name = os.path.join(path, name)
    with open(name, "w") as fp:
        fp.write(source.data)
    return name


# content pacakges

etree_parse = getattr(etree, 'parse')


def content_package_library():
    return component.queryUtility(IContentPackageLibrary)


def get_rendered_package_ntiid(path):
    name = os.path.join(path, 'eclipse-toc.xml')
    tree = etree_parse(name)
    root = tree.getroot()
    package = root.get('ntiid')
    assert package is not None, "Invalid rendered content directory"
    return package


def remove_content(package):
    root = getattr(package, 'root', None) \
        or getattr(package, 'key', None)
    locator = component.getUtility(IRenderedContentLocator)
    return locator.remove(root)


def move_content(library, path):
    enumeration = library.enumeration
    root = getattr(enumeration, 'root', None) \
        or getattr(enumeration, 'bucket', None)
    locator = component.getUtility(IRenderedContentLocator)
    return locator.move(path, root)


def update_library(ntiid, path, library=None, move=True):
    library = content_package_library() if library is None else library
    if library is None:  # tests
        return
    if move:  # move False trx retry
        move_content(library, path)
    package = library.get(ntiid)
    is_new = (
        package is None or get_content_package_site(package) != get_site()
    )
    # enumerate all content packages to build new pkgs
    enumeration = library.enumeration
    content_packages = [
        x for x in enumeration.enumerateContentPackages() if x.ntiid == ntiid
    ]
    assert content_packages and len(content_packages) == 1
    # add or replace
    updated = content_packages[0]
    if not is_new:
        library.replace(updated)
    else:
        library.add(updated)
    return updated


# rendering


def find_renderable(archive):
    if os.path.isfile(archive):
        return archive  # assume renderable
    nti_conf = os.path.join(archive, 'nti_render_conf.ini')
    if os.path.exists(nti_conf):
        config = configparser.ConfigParser()
        with open(nti_conf) as fp:
            config.readfp(fp)
            try:
                tex = config.get(NTI_PROVIDER, 'main')
            except configparser.NoOptionError:
                tex = None
        if tex and os.path.exists(os.path.join(archive, tex)):
            return tex
    tex = os.path.basename(archive) + '.tex'
    if os.path.exists(os.path.join(archive, tex)):
        return os.path.join(archive, tex)
    for name in os.listdir(archive):
        lname = name.lower()
        if lname.endswith('.tex'):
            return os.path.join(archive, name)
    raise ValueError("Cannot find renderable LaTeX file")


def obfuscate_source(source):
    if os.path.isfile(source):
        name, ext = os.path.splitext(source)
        path, name = os.path.split(name)
        name = obfuscate_filename(name)
        result = os.path.join(path, name) + ext
        os.rename(source, result)
    else:
        path, name = os.path.split(source)
        name = obfuscate_filename(name)
        result = os.path.join(path, name)
        os.rename(source, result)
    return result


def prepare_environment():
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
    return os.environ['XHTMLTEMPLATES']


def render_source(source, provider=NTI_PROVIDER, obfuscate=True, docachefile=False):
    # make sure chameleon cache
    cache_dir = os.environ.get('CHAMELEON_CACHE', None)
    if cache_dir and not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    source = os.path.abspath(source)
    archive = process_source(source)
    if obfuscate:
        archive = obfuscate_source(archive)
    tex_file = find_renderable(archive)
    path, _ = os.path.split(tex_file)
    current_dir = os.getcwd()
    xhtmltemplates = os.environ.get('XHTMLTEMPLATES', '')
    try:
        os.chdir(path)
        prepare_environment()
        nti_render(tex_file,
                   provider,
                   load_configs=False,
                   docachefile=docachefile,
                   set_chameleon_cache=False)
    finally:
        os.chdir(current_dir)
        os.environ['XHTMLTEMPLATES'] = xhtmltemplates
    return tex_file


def render_library_job(job):
    logger.info('Rendering content (%s)', job.job_id)
    job_id = job.job_id
    try:
        move = True
        update_job_status(job_id, RUNNING)
        tex_file = get_delimited_item(job_id)
        if tex_file is None:
            tmp_dir = tempfile.mkdtemp()
            # 1. save source to a local path
            source = save_source(job.source, tmp_dir)
            # 2. render contents
            tex_file = render_source(source, job.Provider)
            # 3. save in case of a retry
            save_delimited_item(job_id, tex_file)
        else:
            move = False
            logger.warning("Due to a transaction abort, using data from %s for job %s",
                           tex_file, job_id)
        # 4. Get package info
        out_path = os.path.splitext(tex_file)[0]
        package_ntiid = get_rendered_package_ntiid(out_path)
        # 5. Update library
        update_library(package_ntiid, out_path, move=move)
        # 6. clean on commit
        def after_commit_or_abort(success=False):
            if success:
                update_job_status(job_id, SUCCESS)
                shutil.rmtree(tmp_dir, ignore_errors=True)
        transaction.get().addAfterCommitHook(after_commit_or_abort)
    except Exception as e:  # pylint: disable=broad-except
        logger.exception('Render job %s failed', job_id)
        traceback_msg = text_(format_exception(e))
        job.update_to_failed_state(traceback_msg)
        update_job_status(job_id, FAILED)
        update_job_error(job_id, traceback_msg)
    else:
        logger.info('Render (%s) completed', job_id)
        job.update_to_success_state()
        job.package_ntiid = package_ntiid
        update_job_package_ntiid(job_id, package_ntiid)
        lifecycleevent.modified(job)
    finally:
        lifecycleevent.modified(job)
    return job


def render_job(job_id):
    job = load_job(job_id)
    if job is None:
        update_job_status(job_id, FAILED)
        update_job_error(job_id,
                         simplejson.dumps("Job is missing"))
        logger.error("Job %s is missing", job_id)
    else:
        render_library_job(job)


def render_archive(source, creator, provider=NTI_PROVIDER, site=None):
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
