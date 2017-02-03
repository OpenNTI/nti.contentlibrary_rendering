#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import assert_that
does_not = is_not

from nti.externalization import internalization

from nti.externalization.externalization import to_external_object

from nti.testing.matchers import validly_provides

from nti.contentlibrary_rendering.interfaces import FAILED
from nti.contentlibrary_rendering.interfaces import PENDING

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderJob

from nti.contentlibrary_rendering.model import ContentPackageRenderJob

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingTestLayer


class TestExternalization(ContentlibraryRenderingTestLayer):

    def test_render_job(self):
        ntiid = u'tag:nextthought.com,2011-10:USSC-HTML-Cohen.cohen_v._california'
        job_id = '123456'
        ext_obj = {
            'MimeType': ContentPackageRenderJob.mime_type,
            'JobId': job_id,
            'PackageNTIID': ntiid
        }

        assert_that(internalization.find_factory_for(ext_obj),
                    is_(not_none()))

        internal = internalization.find_factory_for(ext_obj)()
        internalization.update_from_external_object(internal,
                                                    ext_obj,
                                                    require_updater=True)

        assert_that(internal, validly_provides(IContentPackageRenderJob))
        assert_that(internal.job_id, is_(job_id))
        assert_that(internal.PackageNTIID, is_(ntiid))
        assert_that(internal.State, is_(PENDING))

        internal.update_to_failed_state()
        ext_obj = to_external_object(internal)
        assert_that(ext_obj['JobId'], is_(job_id))
        assert_that(ext_obj['PackageNTIID'], is_(ntiid))
        assert_that(ext_obj['State'], is_(FAILED))
