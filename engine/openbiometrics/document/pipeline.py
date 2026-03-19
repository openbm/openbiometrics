"""Document processing pipeline.

Orchestrates document detection, OCR, MRZ parsing, and optional face
extraction from identity documents.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

from openbiometrics.document.detector import DetectedDocument, DocumentDetector
from openbiometrics.document.mrz import MRZParser, MRZResult
from openbiometrics.document.ocr import OCRResult

logger = logging.getLogger(__name__)


@dataclass
class DocumentConfig:
    """Configuration for the document processing pipeline.

    Attributes:
        model_dir: Directory containing OCR or face extraction models.
        enable_ocr: Whether to run full OCR on detected documents.
        enable_mrz: Whether to detect and parse MRZ zones.
        enable_face_extraction: Whether to extract the photo from the document.
    """

    model_dir: str = "./models"
    enable_ocr: bool = True
    enable_mrz: bool = True
    enable_face_extraction: bool = False


@dataclass
class DocumentResult:
    """Complete result from processing a document image.

    Attributes:
        document: Detected document with corners and warped crop, or None.
        ocr: OCR text extraction result, or None if OCR disabled / failed.
        mrz: Parsed MRZ data, or None if MRZ disabled / not found.
        face: Extracted face image from the document photo area, or None.
    """

    document: DetectedDocument | None = None
    ocr: OCRResult | None = None
    mrz: MRZResult | None = None
    face: np.ndarray | None = None


class DocumentPipeline:
    """End-to-end document processing pipeline.

    Orchestrates: detect -> perspective warp -> OCR -> MRZ parse -> face extract.

    Usage:
        pipeline = DocumentPipeline(DocumentConfig(enable_ocr=True, enable_mrz=True))
        result = pipeline.process(image)
        if result.mrz:
            print(f"Name: {result.mrz.surname}, {result.mrz.given_names}")
            print(f"DOB: {result.mrz.date_of_birth}")
    """

    def __init__(self, config: DocumentConfig | None = None):
        """
        Args:
            config: Pipeline configuration. Uses defaults if None.
        """
        self.config = config or DocumentConfig()
        self._detector = DocumentDetector()
        self._mrz_parser = MRZParser() if self.config.enable_mrz else None
        self._ocr: object | None = None  # Lazy-loaded DocumentOCR

    def _ensure_ocr(self):
        """Lazily initialize the OCR engine."""
        if self._ocr is not None:
            return self._ocr

        from openbiometrics.document.ocr import DocumentOCR

        self._ocr = DocumentOCR()
        return self._ocr

    def process(self, image: np.ndarray) -> DocumentResult:
        """Process a document image through the full pipeline.

        Args:
            image: BGR numpy array containing a document.

        Returns:
            DocumentResult with all available extraction results.
        """
        result = DocumentResult()

        if image is None or image.size == 0:
            logger.warning("Empty image passed to DocumentPipeline.process()")
            return result

        # Step 1: Detect document
        detections = self._detector.detect(image)
        if not detections:
            logger.debug("No document detected in image")
            return result

        doc = detections[0]  # Take the largest / most confident
        result.document = doc
        warped = doc.warped

        # Step 2: OCR (full text extraction)
        if self.config.enable_ocr:
            try:
                ocr_engine = self._ensure_ocr()
                result.ocr = ocr_engine.extract(warped)
            except ImportError:
                logger.warning(
                    "OCR skipped: python-doctr is not installed. "
                    "Install with: pip install 'python-doctr[torch]'"
                )
            except Exception as exc:
                logger.error("OCR failed: %s", exc)

        # Step 3: MRZ detection and parsing
        if self._mrz_parser is not None:
            try:
                result.mrz = self._mrz_parser.parse(warped)
            except Exception as exc:
                logger.error("MRZ parsing failed: %s", exc)

        # Step 4: Face extraction from document photo area
        if self.config.enable_face_extraction:
            try:
                result.face = _extract_document_face(warped)
            except Exception as exc:
                logger.error("Face extraction failed: %s", exc)

        return result

    def process_file(self, image_path: str) -> DocumentResult:
        """Process a document image from a file path.

        Args:
            image_path: Path to the document image file.

        Returns:
            DocumentResult with all available extraction results.

        Raises:
            FileNotFoundError: If the image file cannot be read.
        """
        import cv2

        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")
        return self.process(image)


def _extract_document_face(warped: np.ndarray) -> np.ndarray | None:
    """Extract the face photo region from a warped document image.

    Uses a heuristic approach: the photo is typically in the left portion
    of ID cards and passports. Falls back to face detection if available.

    Args:
        warped: Perspective-corrected document image (BGR).

    Returns:
        Cropped face region, or None if not found.
    """
    import cv2

    h, w = warped.shape[:2]

    # Heuristic: face photo is typically in the left 40% of the document,
    # vertically centered in the top 70%
    face_region = warped[int(h * 0.1):int(h * 0.75), int(w * 0.02):int(w * 0.40)]

    if face_region.size == 0:
        return None

    # Try OpenCV's Haar cascade for face detection within the region
    try:
        gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))

        if len(faces) > 0:
            # Take the largest detected face
            faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            x, y, fw, fh = faces_sorted[0]
            return face_region[y:y + fh, x:x + fw]
    except Exception:
        logger.debug("Haar cascade face detection failed, returning heuristic region")

    # Fallback: return the heuristic region
    return face_region
