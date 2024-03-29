#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import has_properties
does_not = is_not

from nti.testing.matchers import validly_provides

from nti.externalization import internalization

from nti.contentlibrary_rendering.interfaces import FAILED
from nti.contentlibrary_rendering.interfaces import PENDING

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderJob

from nti.contentlibrary_rendering.model import ContentPackageRenderJob

from nti.externalization.externalization import to_external_object

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestExternalization(ContentlibraryRenderingLayerTest):

    def test_render_job(self):
        ntiid = u'tag:nextthought.com,2011-10:USSC-HTML-Cohen.cohen_v._california'
        job_id = u'123456'
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
        assert_that(internal,
                    has_properties('JobId', is_(job_id),
                                   'PackageNTIID', is_(ntiid),
                                   'State', is_(PENDING)))
        internal.update_to_failed_state('error')
        ext_obj = to_external_object(internal)
        assert_that(ext_obj,
                    has_entries('JobId', is_(job_id),
                                'PackageNTIID', is_(ntiid),
                                'State', is_(FAILED),
                                'Error', is_('error')))
