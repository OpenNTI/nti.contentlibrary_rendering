#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

def _do_render_package(render_job):
    pass

def render_package_job(render_job):
    try:
        _do_render_package( render_job )
    except Exception:
        logger.exception( 'Render job failed' )
        render_job.update_to_failed_state()
    else:
        render_job.update_to_success_state()
