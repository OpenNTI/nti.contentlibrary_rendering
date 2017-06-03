#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that

from nti.testing.matchers import is_empty

from nti.contentlibrary_rendering.interfaces import FAILED

from nti.contentlibrary_rendering.index import ContentRenderJobCatalog
from nti.contentlibrary_rendering.index import create_contentrenderjob_catalog

from nti.contentlibrary_rendering.model import ContentPackageRenderJob

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingTestLayer


class TestIndex(ContentlibraryRenderingTestLayer):

    def test_catalog(self):
        ntiid = u'tag:nextthought.com,2011-10:USSC-HTML-Cohen.cohen_v._california'
        catalog = create_contentrenderjob_catalog()
        assert_that(catalog, is_not(none()))
        assert_that(catalog, has_length(8))
        assert_that(isinstance(catalog, ContentRenderJobCatalog), is_(True))

        job = ContentPackageRenderJob()
        job.JobId = u'123456'
        job.PackageNTIID = ntiid
        job.State = FAILED
        job.creator = u'ichigo'
        job.updateLastMod()
        catalog.index_doc(1, job)

        for query in (
                {'state': {'any_of': (FAILED,)}},
                {'jobId': {'any_of': ('123456',)}},
                {'creator': {'any_of': ('ichigo',)}},
                {'packageNTIID': {'any_of': (ntiid,)}},
                {'mimeType': {'any_of': ('application/vnd.nextthought.content.packagerenderjob',)}}):
            results = catalog.apply(query) or ()
            assert_that(results, is_not(is_empty()))
