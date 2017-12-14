#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import ends_with
from hamcrest import assert_that
from hamcrest import starts_with
from hamcrest import has_property

import os
import shutil
import tarfile
import tempfile

import fudge
import fakeredis
import simplejson

from zope import interface

from zope.security.interfaces import IPrincipal

from nti.base.interfaces import INamedFile

from nti.contentlibrary_rendering._archive import load_job
from nti.contentlibrary_rendering._archive import store_job
from nti.contentlibrary_rendering._archive import get_job_error
from nti.contentlibrary_rendering._archive import get_job_status
from nti.contentlibrary_rendering._archive import process_source
from nti.contentlibrary_rendering._archive import find_renderable
from nti.contentlibrary_rendering._archive import generate_job_id
from nti.contentlibrary_rendering._archive import format_exception
from nti.contentlibrary_rendering._archive import obfuscate_source
from nti.contentlibrary_rendering._archive import update_job_error
from nti.contentlibrary_rendering._archive import create_render_job
from nti.contentlibrary_rendering._archive import update_job_status
from nti.contentlibrary_rendering._archive import render_library_job
from nti.contentlibrary_rendering._archive import get_job_package_ntiid
from nti.contentlibrary_rendering._archive import update_job_package_ntiid

from nti.ntiids.ntiids import ROOT

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


@interface.implementer(INamedFile)
class _Source(object):
    data = b'ichigo'
    filename = "bleach.zip"


@interface.implementer(IPrincipal)
class _Principal(object):
    id = 'ichigo'
    title = "shinigami"


class TestArchive(ContentlibraryRenderingLayerTest):

    data = b'ichigo and aizen'

    def test_process_source_tar_gz(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            out_name = os.path.join(tmp_dir, 'data.tex')
            with open(out_name, "wb") as fp:
                fp.write(self.data)
            tar_name = os.path.join(tmp_dir, 'data.tar.gz')
            with tarfile.open(tar_name, mode="w:gz") as fp:
                fp.add(out_name, arcname='data.tex')
            source = process_source(tar_name)
            assert_that(source, is_not(none()))
            assert_that(os.path.isdir(source), is_(False))

            latex = find_renderable(source)
            assert_that(latex, is_not(none()))
            assert_that(os.path.isfile(latex), is_(True))
            assert_that(latex, ends_with('data.tex'))

            shutil.rmtree(source, True)
        finally:
            shutil.rmtree(tmp_dir, True)

    @fudge.patch('nti.contentlibrary_rendering._archive.redis_client')
    def test_job_id_ops(self, mock_rc):
        mock_rc.is_callable().with_args().returns(fakeredis.FakeStrictRedis())
        source = _Source()
        jid = generate_job_id(source, "tite kubo")
        assert_that(jid,
                    starts_with('tag:nextthought.com,2011-10:LibraryRenderJob-tite_kubo_bleach_zip_'))

        key = update_job_status(jid, "SUCCESS")
        assert_that(key, starts_with(jid))
        assert_that(key, ends_with("=status"))
        
        assert_that(get_job_status(jid), is_('SUCCESS'))

    @fudge.patch('nti.contentlibrary_rendering._archive.redis_client')
    def test_job_ops(self, mock_rc):
        mock_rc.is_callable().with_args().returns(fakeredis.FakeStrictRedis())
        source = _Source()
        job = create_render_job(source, "tite kubo")
        store_job(job)
        loaded = load_job(job.jobId)
        assert_that(loaded, is_(job))

    def test_render_library_job(self):
        source = _Source()
        source.filename = 'sample.tex'
        path = os.path.join(os.path.dirname(__file__), 'sample.tex')
        with open(path, "rb") as fp:
            source.data = fp.read()
        job = create_render_job(source, _Principal())
        render_library_job(job)
        assert_that(job, has_property('PackageNTIID', is_not(none())))

    def test_format_exception(self):
        try:
            raise Exception('bleach')
        except Exception as e:  # pylint: disable=broad-except
            msg = format_exception(e)
        assert_that(msg, is_not(none()))
        msg = simplejson.loads(msg)
        assert_that(msg, has_entry('message', 'bleach'))
        assert_that(msg, has_entry('code', 'Exception'))
        assert_that(msg, has_entry('traceback',  is_not(none())))
    
    @fudge.patch('nti.contentlibrary_rendering._archive.redis_client')
    def test_job_error(self, mock_rc):
        redis = fakeredis.FakeStrictRedis()
        mock_rc.is_callable().with_args().returns(redis)
        update_job_error("bankai",
                         simplejson.dumps("bleach"))
        error = get_job_error("bankai")
        assert_that(error, has_entry('message', 'bleach'))
        assert_that(error, has_entry('code', 'AssertionError'))
        
    @fudge.patch('nti.contentlibrary_rendering._archive.redis_client')
    def test_job_packate_ntiid(self, mock_rc):
        redis = fakeredis.FakeStrictRedis()
        mock_rc.is_callable().with_args().returns(redis)
        update_job_package_ntiid("jobId", ROOT)
        ntiid = get_job_package_ntiid("jobId")
        assert_that(ntiid, is_(ROOT))
        
    def test_obfuscate_source(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            new_dir = obfuscate_source(tmp_dir)
            assert_that(tmp_dir, is_not(new_dir))
            assert_that(os.path.exists(tmp_dir), is_(False))
            assert_that(os.path.exists(new_dir), is_(True))
            tmp_dir = new_dir
        finally:
            shutil.rmtree(tmp_dir, True)
