import unittest
import pickle
import sys
import tempfile
import os
import shutil

from operator import itemgetter, attrgetter
from StringIO import StringIO

import cloudpickle

class CloudPickleTest(unittest.TestCase):

    def test_itemgetter(self):
        d = range(10)
        getter = itemgetter(1)

        getter2 = pickle.loads(cloudpickle.dumps(getter))
        self.assertEqual(getter(d), getter2(d))

        getter = itemgetter(0, 3)
        getter2 = pickle.loads(cloudpickle.dumps(getter))
        self.assertEqual(getter(d), getter2(d))

    def test_attrgetter(self):
        class C(object):
            def __getattr__(self, item):
                return item
        d = C()
        getter = attrgetter("a")
        getter2 = pickle.loads(cloudpickle.dumps(getter))
        self.assertEqual(getter(d), getter2(d))
        getter = attrgetter("a", "b")
        getter2 = pickle.loads(cloudpickle.dumps(getter))
        self.assertEqual(getter(d), getter2(d))

        d.e = C()
        getter = attrgetter("e.a")
        getter2 = pickle.loads(cloudpickle.dumps(getter))
        self.assertEqual(getter(d), getter2(d))
        getter = attrgetter("e.a", "e.b")
        getter2 = pickle.loads(cloudpickle.dumps(getter))
        self.assertEqual(getter(d), getter2(d))

    def test_xrange_params(self):
        xr = xrange(1,100)
        start, step, length = cloudpickle.xrange_params(xr)
        self.assertEqual(1, start)
        self.assertEqual(1, step)
        self.assertEqual(99, length)

        xr = xrange(20)
        start, step, length = cloudpickle.xrange_params(xr)
        self.assertEqual(0, start)
        self.assertEqual(1, step)
        self.assertEqual(20, length)

        # Arbitrary steps
        import math
        xr = xrange(3,48,2)
        start, step, length = cloudpickle.xrange_params(xr)
        self.assertEqual(3, start)
        self.assertEqual(2, step)
        self.assertEqual(math.ceil((48-3)/2.0), length)

        # Empty xrange
        xr = xrange(50,1,5)
        start, step, length = cloudpickle.xrange_params(xr)
        #self.assertEqual(50, start) # These currently are inferred
        #self.assertEqual(5, step)   # only by the length in Python2
        self.assertEqual(0, length)

        # Single element
        xr = xrange(42,43)
        start, step, length = cloudpickle.xrange_params(xr)
        self.assertEqual(1, length)
        self.assertEqual(42, start)
        self.assertEqual(1, step)


    def test_pickling_xrange(self):
        xr1 = xrange(1,100, 3)
        xr2 = pickle.loads(cloudpickle.dumps(xr1))

        # Can't just `self.assertEquals(xr1, xr2)` because it compares
        # the objects
        for a,b in zip(xr1, xr2):
            self.assertEquals(a,b)

    # Regression test for SPARK-3415
    def test_pickling_special_file_handles(self):
        for out in sys.stdout, sys.stderr:
            self.assertEquals(out, pickle.loads(cloudpickle.dumps(out)))

    def test_pickling_regular_file_handles(self):
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'testfile')
        teststring = 'Hello world!'
        try:
            with open(tmpfile, 'w') as f:
                f.write(teststring)
            with open(tmpfile, 'r') as f:
                self.assertEquals(teststring, pickle.loads(cloudpickle.dumps(f)).read())
        finally:
            shutil.rmtree(tmpdir)

    def FAILING_test_pickling_temp_file(self):
        teststring = 'Hello world!'
        with tempfile.NamedTemporaryFile() as fp:
            fp.write(teststring)
            fp.seek(0)
            f = fp.file
            self.assertEquals(teststring, pickle.loads(cloudpickle.dumps(f)).read())

    def test_func_globals(self):
        class Unpicklable(object):
            def __reduce__(self):
                raise Exception("not picklable")

        global exit
        exit = Unpicklable()

        self.assertRaises(Exception, lambda: cloudpickle.dumps(exit))

        def foo():
            sys.exit(0)

        self.assertTrue("exit" in foo.func_code.co_names)
        cloudpickle.dumps(foo)

    def test_builtin_dicts(self):
        f = dir
        self.assertEquals(f, pickle.loads(cloudpickle.dumps(f)))


if __name__ == '__main__':
    unittest.main()
