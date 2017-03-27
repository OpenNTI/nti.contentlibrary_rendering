#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import ends_with
from hamcrest import assert_that
from hamcrest import starts_with

import os
import bz2
import gzip
import shutil
import tarfile
import tempfile
from io import BytesIO

import fudge
import fakeredis
import simplejson

from zope import interface

from zope.security.interfaces import IPrincipal

from nti.base.interfaces import INamedFile

from nti.contentlibrary_rendering._archive import is_bz2
from nti.contentlibrary_rendering._archive import is_gzip
from nti.contentlibrary_rendering._archive import load_job
from nti.contentlibrary_rendering._archive import store_job
from nti.contentlibrary_rendering._archive import get_job_status
from nti.contentlibrary_rendering._archive import process_source
from nti.contentlibrary_rendering._archive import find_renderable
from nti.contentlibrary_rendering._archive import generate_job_id
from nti.contentlibrary_rendering._archive import format_exception
from nti.contentlibrary_rendering._archive import create_render_job
from nti.contentlibrary_rendering._archive import update_job_status
from nti.contentlibrary_rendering._archive import render_library_job

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

    def test_is_gzip(self):
        bio = BytesIO()
        with gzip.GzipFile(fileobj=bio, mode="wb") as fp:
            fp.write(self.data)
        assert_that(is_gzip(bio), is_(True))

    def test_is_bz2(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            out_name = os.path.join(tmp_dir, 'data.dat')
            with bz2.BZ2File(out_name, mode="wb") as fp:
                fp.write(self.data)
            assert_that(is_bz2(out_name), is_(True))
        finally:
            shutil.rmtree(tmp_dir, True)

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

    def test_format_exception(self):
        try:
            raise Exception('bleach')
        except Exception as e:
            msg = format_exception(e)
        assert_that(msg, is_not(none()))
        msg = simplejson.loads(msg)
        assert_that(msg, has_entry('message', 'bleach'))
        assert_that(msg, has_entry('code', 'Exception'))
        assert_that(msg, has_entry('traceback',  is_not(none())))
