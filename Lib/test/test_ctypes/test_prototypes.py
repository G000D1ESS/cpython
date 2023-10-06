from ctypes import *
from test.test_ctypes import need_symbol
import unittest

# IMPORTANT INFO:
#
# Consider this call:
#    func_.restype = c_char_p
#    func_(c_char_p("123"))
# It returns
#    "123"
#
# WHY IS THIS SO?
#
# argument tuple (c_char_p("123"), ) is destroyed after the function
# func_ is called, but NOT before the result is actually built.
#
# If the arglist would be destroyed BEFORE the result has been built,
# the c_char_p("123") object would already have a zero refcount,
# and the pointer passed to (and returned by) the function would
# probably point to deallocated space.
#
# In this case, there would have to be an additional reference to the argument...

import _ctypes_test
testdll = CDLL(_ctypes_test.__file__)

# Return machine address `a` as a (possibly long) non-negative integer.
# Starting with Python 2.5, id(anything) is always non-negative, and
# the ctypes addressof() inherits that via PyLong_FromVoidPtr().
def positive_address(a):
    if a >= 0:
        return a
    # View the bits in `a` as unsigned instead.
    import struct
    num_bits = struct.calcsize("P") * 8 # num bits in native machine address
    a += 1 << num_bits
    assert a >= 0
    return a

def c_wbuffer(init):
    n = len(init) + 1
    return (c_wchar * n)(*init)

class CharPointersTestCase(unittest.TestCase):

    def setUp(self):
        func_ = testdll._testfunc_p_p
        func_.restype = c_long
        func_.argtypes = None

    def test_paramflags(self):
        # function returns c_void_p result,
        # and has a required parameter named 'input'
        prototype = CFUNCTYPE(c_void_p, c_void_p)
        func_ = prototype(("_testfunc_p_p", testdll),
                         ((1, "input"),))

        try:
            func_()
        except TypeError as details:
            self.assertEqual(str(details), "required argument 'input' missing")
        else:
            self.fail("TypeError not raised")

        self.assertEqual(func_(None), None)
        self.assertEqual(func_(input=None), None)


    def test_int_pointer_arg(self):
        func_ = testdll._testfunc_p_p
        if sizeof(c_longlong) == sizeof(c_void_p):
            func_.restype = c_longlong
        else:
            func_.restype = c_long
        self.assertEqual(0, func_(0))

        ci = c_int(0)

        func_.argtypes = POINTER(c_int),
        self.assertEqual(positive_address(addressof(ci)),
                             positive_address(func_(byref(ci))))

        func_.argtypes = c_char_p,
        self.assertRaises(ArgumentError, func_, byref(ci))

        func_.argtypes = POINTER(c_short),
        self.assertRaises(ArgumentError, func_, byref(ci))

        func_.argtypes = POINTER(c_double),
        self.assertRaises(ArgumentError, func_, byref(ci))

    def test_POINTER_c_char_arg(self):
        func_ = testdll._testfunc_p_p
        func_.restype = c_char_p
        func_.argtypes = POINTER(c_char),

        self.assertEqual(None, func_(None))
        self.assertEqual(b"123", func_(b"123"))
        self.assertEqual(None, func_(c_char_p(None)))
        self.assertEqual(b"123", func_(c_char_p(b"123")))

        self.assertEqual(b"123", func_(c_buffer(b"123")))
        ca = c_char(b"a")
        self.assertEqual(ord(b"a"), func_(pointer(ca))[0])
        self.assertEqual(ord(b"a"), func_(byref(ca))[0])

    def test_c_char_p_arg(self):
        func_ = testdll._testfunc_p_p
        func_.restype = c_char_p
        func_.argtypes = c_char_p,

        self.assertEqual(None, func_(None))
        self.assertEqual(b"123", func_(b"123"))
        self.assertEqual(None, func_(c_char_p(None)))
        self.assertEqual(b"123", func_(c_char_p(b"123")))

        self.assertEqual(b"123", func_(c_buffer(b"123")))
        ca = c_char(b"a")
        self.assertEqual(ord(b"a"), func_(pointer(ca))[0])
        self.assertEqual(ord(b"a"), func_(byref(ca))[0])

    def test_c_void_p_arg(self):
        func_ = testdll._testfunc_p_p
        func_.restype = c_char_p
        func_.argtypes = c_void_p,

        self.assertEqual(None, func_(None))
        self.assertEqual(b"123", func_(b"123"))
        self.assertEqual(b"123", func_(c_char_p(b"123")))
        self.assertEqual(None, func_(c_char_p(None)))

        self.assertEqual(b"123", func_(c_buffer(b"123")))
        ca = c_char(b"a")
        self.assertEqual(ord(b"a"), func_(pointer(ca))[0])
        self.assertEqual(ord(b"a"), func_(byref(ca))[0])

        func_(byref(c_int()))
        func_(pointer(c_int()))
        func_((c_int * 3)())

    @need_symbol('c_wchar_p')
    def test_c_void_p_arg_with_c_wchar_p(self):
        func_ = testdll._testfunc_p_p
        func_.restype = c_wchar_p
        func_.argtypes = c_void_p,

        self.assertEqual(None, func_(c_wchar_p(None)))
        self.assertEqual("123", func_(c_wchar_p("123")))

    def test_instance(self):
        func_ = testdll._testfunc_p_p
        func_.restype = c_void_p

        class X:
            _as_parameter_ = None

        func_.argtypes = c_void_p,
        self.assertEqual(None, func_(X()))

        func_.argtypes = None
        self.assertEqual(None, func_(X()))

@need_symbol('c_wchar')
class WCharPointersTestCase(unittest.TestCase):

    def setUp(self):
        func_ = testdll._testfunc_p_p
        func_.restype = c_int
        func_.argtypes = None


    def test_POINTER_c_wchar_arg(self):
        func_ = testdll._testfunc_p_p
        func_.restype = c_wchar_p
        func_.argtypes = POINTER(c_wchar),

        self.assertEqual(None, func_(None))
        self.assertEqual("123", func_("123"))
        self.assertEqual(None, func_(c_wchar_p(None)))
        self.assertEqual("123", func_(c_wchar_p("123")))

        self.assertEqual("123", func_(c_wbuffer("123")))
        ca = c_wchar("a")
        self.assertEqual("a", func_(pointer(ca))[0])
        self.assertEqual("a", func_(byref(ca))[0])

    def test_c_wchar_p_arg(self):
        func_ = testdll._testfunc_p_p
        func_.restype = c_wchar_p
        func_.argtypes = c_wchar_p,

        c_wchar_p.from_param("123")

        self.assertEqual(None, func_(None))
        self.assertEqual("123", func_("123"))
        self.assertEqual(None, func_(c_wchar_p(None)))
        self.assertEqual("123", func_(c_wchar_p("123")))

        # XXX Currently, these raise TypeErrors, although they shouldn't:
        self.assertEqual("123", func_(c_wbuffer("123")))
        ca = c_wchar("a")
        self.assertEqual("a", func_(pointer(ca))[0])
        self.assertEqual("a", func_(byref(ca))[0])

class ArrayTest(unittest.TestCase):
    def test(self):
        func_ = testdll._testfunc_ai8
        func_.restype = POINTER(c_int)
        func_.argtypes = c_int * 8,

        func_((c_int * 8)(1, 2, 3, 4, 5, 6, 7, 8))

        # This did crash before:

        def func_(): pass
        CFUNCTYPE(None, c_int * 3)(func_)

################################################################

if __name__ == '__main__':
    unittest.main()
