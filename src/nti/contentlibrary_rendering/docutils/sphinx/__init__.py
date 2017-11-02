#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import logging
import tempfile

try:
    from sphinx import application

    # reduce verbosity
    logger = application.logger
    logger.setLevel(logging.ERROR)

    def create_sphinx(srcdir=None,
                      confdir=None,
                      outdir=None,
                      doctreedir=None,
                      buildername='html'):
        # set defaults
        outdir = outdir or tempfile.gettempdir()
        srcdir = srcdir or os.path.dirname(__file__)
        confdir = confdir or os.path.dirname(__file__)
        doctreedir = doctreedir or os.path.dirname(__file__)
        # return app
        return application.Sphinx(srcdir, confdir,
                                  outdir, doctreedir, buildername)
except ImportError:
    def create_sphinx(*args, **kwargs):
        pass
