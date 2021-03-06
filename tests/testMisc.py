from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
from fontTools.misc.py23 import PY3
import sys
import os
import unittest
import io
import drawBot
from drawBot.misc import DrawBotError, warnings
from drawBot.scriptTools import ScriptRunner
from testSupport import StdOutCollector, testDataDir


class MiscTest(unittest.TestCase):

    def test_polygon_notEnoughPoints(self):
        drawBot.newDrawing()
        with self.assertRaises(TypeError):
            drawBot.polygon()
        with self.assertRaises(TypeError):
            drawBot.polygon((1, 2))
        drawBot.polygon((1, 2), (3, 4))

    def test_polygon_unexpectedKeywordArgument(self):
        drawBot.newDrawing()
        drawBot.polygon((1, 2), (3, 4), close=True)
        drawBot.polygon((1, 2), (3, 4), close=False)
        with self.assertRaises(TypeError):
            drawBot.polygon((1, 2), (3, 4), closed=False)
        with self.assertRaises(TypeError):
            drawBot.polygon((1, 2), (3, 4), closed=False, foo=123)

    def test_ScriptRunner_StdOutCollector(self):
        out = StdOutCollector()
        ScriptRunner("print('hey!')", stdout=out, stderr=out)
        self.assertEqual(out, ["hey!"])

    def test_ScriptRunner_io(self):
        if PY3:
            MyStringIO = io.StringIO
        else:
            class MyStringIO(io.StringIO):
                def write(self, value):
                    if not isinstance(value, unicode):
                        value = value.decode("utf8")
                    super(MyStringIO, self).write(value)
        out = MyStringIO()
        ScriptRunner("print('hey!')", stdout=out, stderr=out)
        self.assertEqual(out.getvalue(), u'hey!\n')
        out = MyStringIO()
        ScriptRunner("print(u'hey!')", stdout=out, stderr=out)
        self.assertEqual(out.getvalue(), u'hey!\n')
        out = MyStringIO()
        ScriptRunner(u"print('hey!')", stdout=out, stderr=out)
        self.assertEqual(out.getvalue(), u'hey!\n')
        out = MyStringIO()
        ScriptRunner(u"print(u'hey!')", stdout=out, stderr=out)
        self.assertEqual(out.getvalue(), u'hey!\n')

    def test_ScriptRunner_print_function(self):
        out = StdOutCollector()
        ScriptRunner("print 'hey!'", stdout=out, stderr=out)
        if PY3:
            self.assertEqual(out[-1], "SyntaxError: Missing parentheses in call to 'print'. Did you mean print('hey!')?")
        else:
            self.assertEqual(out, ["hey!"])

    def test_ScriptRunner_division(self):
        out = StdOutCollector()
        ScriptRunner("print(1/2)", stdout=out, stderr=out)
        self.assertEqual(out, ["0.5"])

    def test_ScriptRunner_oldDivision(self):
        realGetDefault = drawBot.scriptTools.getDefault
        def mockedGetDefault(*args):
            return False
        drawBot.scriptTools.getDefault = mockedGetDefault
        try:
            out = StdOutCollector()
            ScriptRunner("print(1/2)", stdout=out, stderr=out)
            if PY3:
                self.assertEqual(out, ["0.5"])
            else:
                self.assertEqual(out, ["0"])
        finally:
            drawBot.scriptTools.getDefault = realGetDefault

    def test_ScriptRunner_encoding(self):
        out = StdOutCollector()
        ScriptRunner("# -*- coding: utf-8 -*-\nprint(1/2)", stdout=out, stderr=out)
        self.assertEqual(out, ["0.5"])
        out = StdOutCollector()
        ScriptRunner(u"# -*- coding: utf-8 -*-\nprint(1/2)", stdout=out, stderr=out)
        self.assertEqual(out, ["0.5"])

    def test_ScriptRunner_file(self):
        out = StdOutCollector()
        path = os.path.join(testDataDir, "scriptRunnerTest.py") # use an actual file, no not confuse coverage testing
        ScriptRunner("print(__file__)\nprint(__name__)", stdout=out, stderr=out, path=path)
        self.assertEqual(out, [path, "__main__"])

    def test_ScriptRunner_fromPath(self):
        out = StdOutCollector()
        path = os.path.join(testDataDir, "scriptRunnerTest.py")
        ScriptRunner(path=path, stdout=out, stderr=out)
        self.assertEqual(out, [path, "__main__", u'\xc5benr\xe5'])

    def test_ScriptRunner_namespace(self):
        out = StdOutCollector()
        ScriptRunner("print(aaaa)", stdout=out, stderr=out, namespace=dict(aaaa=123))
        self.assertEqual(out, ["123"])

    def test_ScriptRunner_checkSyntaxOnly(self):
        out = StdOutCollector()
        ScriptRunner("print(aaaa)", stdout=out, stderr=out, checkSyntaxOnly=True)
        self.assertEqual(out, [])
        out = StdOutCollector()
        ScriptRunner("print('hello world!')", stdout=out, stderr=out, checkSyntaxOnly=False)
        self.assertEqual(out, ['hello world!'])
        out = StdOutCollector()
        ScriptRunner("print('hello world!')", stdout=out, stderr=out, checkSyntaxOnly=True)
        self.assertEqual(out, [])
        out = StdOutCollector()
        ScriptRunner("aaa bbb", stdout=out, stderr=out, checkSyntaxOnly=True)
        self.assertEqual(out[-1], 'SyntaxError: invalid syntax')


if __name__ == '__main__':
    sys.exit(unittest.main())
