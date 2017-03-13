#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that
from hamcrest import starts_with
from hamcrest import contains_string

import fudge

import os
import socket
import shutil
import tempfile

from nti.contentlibrary.filesystem import FilesystemBucket

from nti.contentlibrary_rendering.locators import FilesystemLocator

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestLocator(ContentlibraryRenderingLayerTest):

    @fudge.patch('nti.contentlibrary_rendering.locators.FilesystemLocator._get_id')
    def test_filelocator(self, m_gid):
        m_gid.is_callable().with_args().returns("1000")
        sample = os.path.join(os.path.dirname(__file__), 'sample.tex')
        source_dir = tempfile.mkdtemp()
        target_dir = tempfile.mkdtemp()
        try:
            shutil.copy(sample, source_dir + "/sample.tex")
            locator = FilesystemLocator()
            root = FilesystemBucket(name="source")
            root.absolute_path = target_dir
            bucket = locator._do_locate(source_dir, root=root, context=None)
            assert_that(bucket, is_not(none()))
            assert_that(bucket.absolute_path, contains_string("_authored_"))
            assert_that(bucket.absolute_path, contains_string(socket.gethostname()))
            assert_that(bucket.absolute_path, contains_string("_1000"))
            assert_that(bucket.absolute_path, starts_with(target_dir))
            assert_that(os.path.exists(bucket.absolute_path), is_(True))
            assert_that(os.path.isdir(bucket.absolute_path), is_(True))
            assert_that(os.path.exists(source_dir), is_(False))
            assert_that(os.path.exists(os.path.join(bucket.absolute_path, 'sample.tex')),
                        is_(True))
        finally:
            shutil.rmtree(source_dir, True)
            shutil.rmtree(target_dir, True)
