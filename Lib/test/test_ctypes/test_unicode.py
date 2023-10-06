import unittest
import ctypes
from test.test_ctypes import need_symbol

import _ctypes_test

@need_symbol('c_wchar')
class UnicodeTestCase(unittest.TestCase):
    def test_wcslen(self):
        dll = ctypes.CDLL(_ctypes_test.__file__)
        wcslen = dll.my_wcslen
        wcslen.argtypes = [ctypes.c_wchar_p]

        self.assertEqual(wcslen("abc"), 3)
        self.assertEqual(wcslen("ab\u2070"), 3)
        self.assertRaises(ctypes.ArgumentError, wcslen, b"ab\xe4")

    def test_buffers(self):
        buf = ctypes.create_unicode_buffer("abc")
        self.assertEqual(len(buf), 3+1)

        buf = ctypes.create_unicode_buffer("ab\xe4\xf6\xfc")
        self.assertEqual(buf[:], "ab\xe4\xf6\xfc\0")
        self.assertEqual(buf[::], "ab\xe4\xf6\xfc\0")
        self.assertEqual(buf[::-1], '\x00\xfc\xf6\xe4ba')
        self.assertEqual(buf[::2], 'a\xe4\xfc')
        self.assertEqual(buf[6:5:-1], "")

    def test_embedded_null(self):
        class TestStruct(ctypes.Structure):
            _fields_ = [("unicode", ctypes.c_wchar_p)]
        t = TestStruct()
        # This would raise a ValueError:
        t.unicode = "foo\0bar\0\0"


func_ = ctypes.CDLL(_ctypes_test.__file__)._testfunc_p_p

class StringTestCase(UnicodeTestCase):
    def setUp(self):
        func_.argtypes = [ctypes.c_char_p]
        func_.restype = ctypes.c_char_p

    def tearDown(self):
        func_.argtypes = None
        func_.restype = ctypes.c_int

    def test_func(self):
        self.assertEqual(func_(b"abc\xe4"), b"abc\xe4")

    def test_buffers(self):
        buf = ctypes.create_string_buffer(b"abc")
        self.assertEqual(len(buf), 3+1)

        buf = ctypes.create_string_buffer(b"ab\xe4\xf6\xfc")
        self.assertEqual(buf[:], b"ab\xe4\xf6\xfc\0")
        self.assertEqual(buf[::], b"ab\xe4\xf6\xfc\0")
        self.assertEqual(buf[::-1], b'\x00\xfc\xf6\xe4ba')
        self.assertEqual(buf[::2], b'a\xe4\xfc')
        self.assertEqual(buf[6:5:-1], b"")


if __name__ == '__main__':
    unittest.main()
