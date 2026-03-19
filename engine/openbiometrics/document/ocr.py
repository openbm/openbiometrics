"""Optical character recognition for document images.

Uses python-doctr for text extraction. The doctr dependency is optional —
an informative error is raised if it is not installed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TextLine:
    """A single line of text extracted from a document.

    Attributes:
        text: Recognized text content.
        bbox: Bounding box as [x_min, y_min, x_max, y_max] in normalized [0, 1] coordinates.
        confidence: OCR confidence for this line [0, 1].
    """

    text: str
    bbox: list[float]
    confidence: float


@dataclass
class OCRResult:
    """Complete OCR result for a document image.

    Attributes:
        full_text: All recognized text joined with newlines.
        lines: Individual text lines with positions and confidence.
        confidence: Average confidence across all lines [0, 1].
    """

    full_text: str
    lines: list[TextLine] = field(default_factory=list)
    confidence: float = 0.0


def _import_doctr():
    """Lazily import doctr, raising a helpful error if not installed."""
    try:
        from doctr.io import DocumentFile
        from doctr.models import ocr_predictor
        return DocumentFile, ocr_predictor
    except ImportError as exc:
        raise ImportError(
            "python-doctr is required for OCR but is not installed. "
            "Install it with: pip install 'python-doctr[torch]' or "
            "pip install 'python-doctr[tf]'. "
            "See https://github.com/mindee/doctr for details."
        ) from exc


class DocumentOCR:
    """OCR engine for document text extraction using doctr.

    Models are loaded lazily on first use to avoid startup cost when
    OCR is not needed.

    Usage:
        ocr = DocumentOCR()
        result = ocr.extract(document_image)
        print(result.full_text)
    """

    def __init__(self, det_arch: str = "db_resnet50", reco_arch: str = "crnn_vgg16_bn"):
        """
        Args:
            det_arch: doctr text detection architecture name.
            reco_arch: doctr text recognition architecture name.
        """
        self._det_arch = det_arch
        self._reco_arch = reco_arch
        self._predictor = None

    def _ensure_loaded(self) -> None:
        """Load the OCR model on first use."""
        if self._predictor is not None:
            return

        _, ocr_predictor = _import_doctr()
        logger.info("Loading doctr OCR models (det=%s, reco=%s)", self._det_arch, self._reco_arch)
        self._predictor = ocr_predictor(
            det_arch=self._det_arch,
            reco_arch=self._reco_arch,
            pretrained=True,
        )
        logger.info("doctr OCR models loaded")

    def extract(self, image: np.ndarray) -> OCRResult:
        """Extract text from a document image.

        Args:
            image: BGR or RGB numpy array of the document.

        Returns:
            OCRResult with extracted text, line positions, and confidence.

        Raises:
            ImportError: If python-doctr is not installed.
            ValueError: If the input image is invalid.
        """
        if image is None or image.size == 0:
            raise ValueError("Input image is empty or None")

        self._ensure_loaded()

        # doctr expects a list of numpy arrays (pages)
        result = self._predictor([image])

        lines: list[TextLine] = []
        all_text_parts: list[str] = []

        for page in result.pages:
            for block in page.blocks:
                for line in block.lines:
                    words = [word.value for word in line.words]
                    word_confs = [word.confidence for word in line.words]

                    line_text = " ".join(words)
                    line_conf = sum(word_confs) / len(word_confs) if word_confs else 0.0

                    # Line geometry: union of word bboxes
                    # doctr provides (x_min, y_min, x_max, y_max) normalized coords
                    bbox = list(line.geometry) if hasattr(line, "geometry") else [0.0, 0.0, 0.0, 0.0]
                    if isinstance(bbox, (list, tuple)) and len(bbox) == 2:
                        # doctr geometry is ((x_min, y_min), (x_max, y_max))
                        bbox = [bbox[0][0], bbox[0][1], bbox[1][0], bbox[1][1]]

                    lines.append(TextLine(
                        text=line_text,
                        bbox=bbox,
                        confidence=round(line_conf, 3),
                    ))
                    all_text_parts.append(line_text)

        full_text = "\n".join(all_text_parts)
        avg_conf = sum(l.confidence for l in lines) / len(lines) if lines else 0.0

        return OCRResult(
            full_text=full_text,
            lines=lines,
            confidence=round(avg_conf, 3),
        )
