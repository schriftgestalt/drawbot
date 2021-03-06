from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
import sys
import os
import unittest
import glob
import drawBot
import random
import AppKit
from drawBot.context.tools.gifTools import gifFrameCount
from drawBot.misc import DrawBotError
from testSupport import StdOutCollector, TempFile, TempFolder, randomSeed


class ExportTest(unittest.TestCase):

    def makeTestAnimation(self, numFrames=25):
        randomSeed(0)
        drawBot.newDrawing()
        for i in range(numFrames):
            drawBot.newPage(500, 500)
            drawBot.frameDuration(1/25)
            drawBot.fill(1)
            drawBot.rect(0, 0, 500, 500)
            drawBot.fill(0)
            drawBot.rect(random.randint(0, 100), random.randint(0, 100), 400, 400)

    def makeTestDrawing(self):
        drawBot.newDrawing()
        drawBot.newPage(500, 500)
        drawBot.oval(100, 100, 300, 300)

    def _saveImageAndReturnSize(self, extension, **options):
        with TempFile(suffix=extension) as tmp:
            drawBot.saveImage(tmp.path, **options)
            fileSize = os.stat(tmp.path).st_size
        return fileSize

    def test_ffmpegCodec(self):
        self.makeTestAnimation()
        size_h264 = self._saveImageAndReturnSize(".mp4")
        size_mpeg4 = self._saveImageAndReturnSize(".mp4", ffmpegCodec="mpeg4")
        self.assertLess(size_h264, size_mpeg4, "encoded with h264 is expected to be smaller than with mpeg4")

    def test_arbitraryOption(self):
        self.makeTestAnimation(1)
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".png", someArbitraryOption="foo")
        self.assertEqual(output, ['*** DrawBot warning: Unrecognized saveImage() option found for PNGContext: someArbitraryOption ***'])

    def test_export_mov(self):
        self.makeTestAnimation(5)
        self._saveImageAndReturnSize(".mov")

    def test_export_gif(self):
        self.makeTestAnimation(5)
        self._saveImageAndReturnSize(".gif")

    def test_export_png(self):
        self.makeTestDrawing()
        self._saveImageAndReturnSize(".png")

    def test_export_jpg(self):
        self.makeTestDrawing()
        self._saveImageAndReturnSize(".jpg")

    def test_export_jpeg(self):
        self.makeTestDrawing()
        self._saveImageAndReturnSize(".jpeg")

    def test_export_tif(self):
        self.makeTestDrawing()
        self._saveImageAndReturnSize(".tif")

    def test_export_tiff(self):
        self.makeTestDrawing()
        self._saveImageAndReturnSize(".tiff")

    def test_export_bmp(self):
        self.makeTestDrawing()
        self._saveImageAndReturnSize(".bmp")

    def test_imageResolution(self):
        self.makeTestDrawing()
        with TempFile(suffix=".png") as tmp:
            drawBot.saveImage(tmp.path)
            self.assertEqual(drawBot.imageSize(tmp.path), (500, 500))
            drawBot.saveImage(tmp.path, imageResolution=144)
            self.assertEqual(drawBot.imageSize(tmp.path), (1000, 1000))
            drawBot.saveImage(tmp.path, imageResolution=36)
            self.assertEqual(drawBot.imageSize(tmp.path), (250, 250))
            drawBot.saveImage(tmp.path, imageResolution=18)
            self.assertEqual(drawBot.imageSize(tmp.path), (125, 125))

    def test_imagePNGInterlaced(self):
        self.makeTestDrawing()
        defaultSize = self._saveImageAndReturnSize(".png")
        interlacedSize = self._saveImageAndReturnSize(".png", imagePNGInterlaced=True)
        # XXX Huh, seems to make no difference, output files are identical
        self.assertEqual(defaultSize, interlacedSize)

    def test_imagePNGGamma(self):
        self.makeTestDrawing()
        defaultSize = self._saveImageAndReturnSize(".png")
        gammaSize = self._saveImageAndReturnSize(".png", imagePNGGamma=0.8)
        self.assertLess(defaultSize, gammaSize)

    def test_imageJPEGProgressive(self):
        self.makeTestDrawing()
        defaultSize = self._saveImageAndReturnSize(".jpg")
        progressiveSize = self._saveImageAndReturnSize(".jpg", imageJPEGProgressive=True)
        self.assertGreater(defaultSize, progressiveSize)

    def test_imageJPEGCompressionFactor(self):
        self.makeTestDrawing()
        lowCompressionSize = self._saveImageAndReturnSize(".jpg", imageJPEGCompressionFactor=1.0)
        mediumCompressionSize = self._saveImageAndReturnSize(".jpg", imageJPEGCompressionFactor=0.5)
        highCompressionSize = self._saveImageAndReturnSize(".jpg", imageJPEGCompressionFactor=0.0)
        self.assertGreater(lowCompressionSize, mediumCompressionSize)
        self.assertGreater(mediumCompressionSize, highCompressionSize)

    def test_imageTIFFCompressionMethod(self):
        self.makeTestDrawing()
        defaultCompressionSize = self._saveImageAndReturnSize(".tif")
        noCompressionSize = self._saveImageAndReturnSize(".tif", imageTIFFCompressionMethod=None)
        packbitsCompressionSize = self._saveImageAndReturnSize(".tif", imageTIFFCompressionMethod="packbits")
        packbits2CompressionSize = self._saveImageAndReturnSize(".tif", imageTIFFCompressionMethod=32773)
        packbits3CompressionSize = self._saveImageAndReturnSize(".tif", imageTIFFCompressionMethod="PACKBITS")
        lzwCompressionSize = self._saveImageAndReturnSize(".tif", imageTIFFCompressionMethod="lzw")
        self.assertEqual(defaultCompressionSize, noCompressionSize)
        self.assertEqual(packbitsCompressionSize, packbits2CompressionSize)
        self.assertEqual(packbitsCompressionSize, packbits3CompressionSize)
        self.assertGreater(noCompressionSize, packbitsCompressionSize)
        self.assertGreater(packbitsCompressionSize, lzwCompressionSize)

    def test_imageFallbackBackgroundColor(self):
        self.makeTestDrawing()
        with TempFile(suffix=".jpg") as tmp:
            drawBot.saveImage(tmp.path, imageJPEGCompressionFactor=1.0)
            self.assertEqual(drawBot.imagePixelColor(tmp.path, (5, 5)), (1.0, 1.0, 1.0, 1.0))
        with TempFile(suffix=".jpg") as tmp:
            drawBot.saveImage(tmp.path, imageJPEGCompressionFactor=1.0, imageFallbackBackgroundColor=(0, 1, 0))
            r, g, b, a = drawBot.imagePixelColor(tmp.path, (5, 5))
            self.assertEqual((round(r, 2), round(g, 2), round(b, 2)), (0, 0.97, 0))  # XXX 0.97 vs 1.0 "calibrated" vs "device"
        with TempFile(suffix=".jpg") as tmp:
            drawBot.saveImage(tmp.path, imageJPEGCompressionFactor=1.0, imageFallbackBackgroundColor=AppKit.NSColor.redColor())
            r, g, b, a = drawBot.imagePixelColor(tmp.path, (5, 5))
            self.assertEqual((round(r, 2), round(g, 2), round(b, 2)), (1, 0.15, 0))

    def _testMultipage(self, extension, numFrames, expectedMultipageCount):
        self.makeTestAnimation(numFrames)
        with TempFolder() as tmpFolder:
            with TempFile(suffix=extension, dir=tmpFolder.path) as tmp:
                base, ext = os.path.splitext(tmp.path)
                pattern = base + "_*" + ext
                self.assertEqual(len(glob.glob(pattern)), 0)
                drawBot.saveImage(tmp.path)
                self.assertEqual(len(glob.glob(pattern)), 0)
                drawBot.saveImage(tmp.path, multipage=False)
                self.assertEqual(len(glob.glob(pattern)), 0)
                drawBot.saveImage(tmp.path, multipage=True)
                self.assertEqual(len(glob.glob(pattern)), expectedMultipageCount)
        assert not os.path.exists(tmpFolder.path)  # verify TempFolder cleanup

    def test_multipage_png(self):
        self._testMultipage(".png", numFrames=5, expectedMultipageCount=5)

    def test_multipage_jpg(self):
        self._testMultipage(".jpg", numFrames=6, expectedMultipageCount=6)

    def test_multipage_svg(self):
        self._testMultipage(".svg", numFrames=7, expectedMultipageCount=7)

    def test_multipage_gif(self):
        self._testMultipage(".gif", numFrames=8, expectedMultipageCount=0)

    def test_multipage_pdf(self):
        self._testMultipage(".pdf", numFrames=9, expectedMultipageCount=0)

    def test_animatedGIF(self):
        self.makeTestAnimation(5)
        with TempFile(suffix=".gif") as tmp:
            drawBot.saveImage(tmp.path)
            self.assertEqual(gifFrameCount(tmp.path), 5)

    def test_saveImage_unknownContext(self):
        self.makeTestDrawing()
        with self.assertRaises(DrawBotError) as cm:
            drawBot.saveImage("foo.abcde")
        self.assertEqual(cm.exception.args[0], "Could not find a supported context for: 'abcde'")
        with self.assertRaises(DrawBotError) as cm:
            with StdOutCollector(captureStdErr=True) as output:
                drawBot.saveImage(["foo.abcde"])
        self.assertEqual(output, ['*** DrawBot warning: saveImage([path, path, ...]) is deprecated, use multiple saveImage statements. ***'])
        self.assertEqual(cm.exception.args[0], "Could not find a supported context for: 'abcde'")

    def test_saveImage_pathList(self):
        self.makeTestDrawing()
        with self.assertRaises(TypeError) as cm:
            drawBot.saveImage(["foo.abcde"], foo=123)
        self.assertEqual(cm.exception.args[0], 'Cannot apply saveImage options to multiple output formats.')

    def test_saveImage_png_multipage(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".png", multipage=False)
        self.assertEqual(output, [])

    def test_saveImage_png_ffmpegCodec(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".png", ffmpegCodec="mpeg4")
        self.assertEqual(output, ['*** DrawBot warning: Unrecognized saveImage() option found for PNGContext: ffmpegCodec ***'])

    def test_saveImage_mp4_ffmpegCodec(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".mp4", ffmpegCodec="mpeg4")
        self.assertEqual(output, [])

    def test_saveImage_mp4_imageResolution(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".mp4", imageResolution=36)
        self.assertEqual(output, [])

    def test_saveImage_mp4_imagePNGGamma(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".mp4", imagePNGGamma=0.5)
        self.assertEqual(output, [])

    def test_saveImage_mp4_imageJPEGCompressionFactor(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".mp4", imageJPEGCompressionFactor=0.5)
        self.assertEqual(output, ['*** DrawBot warning: Unrecognized saveImage() option found for MP4Context: imageJPEGCompressionFactor ***'])

    def test_saveImage_mp4_multipage(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".mp4", multipage=True)
        self.assertEqual(output, ['*** DrawBot warning: Unrecognized saveImage() option found for MP4Context: multipage ***'])

    def test_saveImage_multipage_positionalArgument(self):
        self.makeTestDrawing()
        with TempFile(suffix=".png") as tmp:
            with StdOutCollector(captureStdErr=True) as output:
                drawBot.saveImage(tmp.path, False)
        self.assertEqual(output, ["*** DrawBot warning: 'multipage' should be a keyword argument: use 'saveImage(path, multipage=True)' ***"])

    def test_saveImage_multiplePositionalArguments(self):
        self.makeTestDrawing()
        with self.assertRaises(TypeError):
            drawBot.saveImage("*", False, "foo")

    def test_saveImage_multipage_keywordArgument(self):
        self.makeTestDrawing()
        with TempFile(suffix=".png") as tmp:
            with StdOutCollector(captureStdErr=True) as output:
                drawBot.saveImage(tmp.path, multipage=False)
        self.assertEqual(output, [])


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    sys.exit(unittest.main())
