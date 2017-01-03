# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import PortalFilesTester
import unittest

"""
Runs the tests suites.
Test suites should be turned on here to run.
"""

__author__ = "Timothy Tickle"
__copyright__ = "Copyright 2016"
__credits__ = ["Timothy Tickle", "Brian Haas"]
__license__ = "MIT"
__maintainer__ = "Timothy Tickle"
__email__ = "ttickle@broadinstitute.org"
__status__ = "Development"


# Calls all unit tests as a regression suite.
suite = unittest.TestSuite()
suite.addTest(PortalFilesTester.suite())
runner = unittest.TextTestRunner()
runner.run(suite)
