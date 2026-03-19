"""Document processing module for OpenBiometrics.

Provides document detection, OCR, MRZ parsing, and face extraction
from identity documents (ID cards, passports, travel documents).
"""

from openbiometrics.document.detector import DetectedDocument, DocumentDetector
from openbiometrics.document.mrz import MRZParser, MRZResult
from openbiometrics.document.ocr import DocumentOCR, OCRResult, TextLine
from openbiometrics.document.pipeline import DocumentConfig, DocumentPipeline, DocumentResult

__all__ = [
    "DetectedDocument",
    "DocumentConfig",
    "DocumentDetector",
    "DocumentOCR",
    "DocumentPipeline",
    "DocumentResult",
    "MRZParser",
    "MRZResult",
    "OCRResult",
    "TextLine",
]
