#!/usr/bin/env python3

import coverage
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

omit_list = ['*/site-packages/*',
             '*/dist-packages/*',
            ]

if __name__ == '__main__':
    cov = coverage.Coverage(cover_pylib=False, omit=omit_list)
    cov.start()

    import tests

    suite = unittest.TestLoader().loadTestsFromModule(tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

    cov.stop()
    cov.save()

    cov.report(show_missing=True, sort='+Name')
