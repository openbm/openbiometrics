"""Machine Readable Zone (MRZ) detection and parsing.

Implements ICAO 9303 MRZ parsing for TD1 (ID cards, 3 lines x 30 chars),
TD2 (travel documents, 2 lines x 36 chars), and TD3 (passports, 2 lines x 44 chars).

The parser is pure Python and works standalone with text input.
Image-based MRZ detection uses OpenCV morphological operations.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ICAO 9303 check digit weights (repeating cycle)
_CHECK_WEIGHTS = [7, 3, 1]

# Character to numeric value mapping for check digit computation
_CHAR_VALUES: dict[str, int] = {"<": 0}
_CHAR_VALUES.update({str(i): i for i in range(10)})
_CHAR_VALUES.update({chr(c): c - 55 for c in range(65, 91)})  # A=10, B=11, ..., Z=35

# Valid MRZ characters
_MRZ_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")


@dataclass
class MRZResult:
    """Parsed MRZ data.

    Attributes:
        mrz_type: Document format — "TD1", "TD2", or "TD3".
        document_number: Document / passport number.
        surname: Holder's surname.
        given_names: Holder's given name(s).
        nationality: Three-letter nationality code.
        date_of_birth: Date of birth as YYMMDD string.
        sex: Sex indicator ("M", "F", or "<").
        expiry_date: Document expiry date as YYMMDD string.
        issuing_country: Three-letter issuing state code.
        raw_mrz: Original MRZ lines.
        check_digits_valid: Whether all ICAO check digits passed validation.
        optional_data_1: First optional data field (if present).
        optional_data_2: Second optional data field (TD1 only, if present).
    """

    mrz_type: str
    document_number: str
    surname: str
    given_names: str
    nationality: str
    date_of_birth: str
    sex: str
    expiry_date: str
    issuing_country: str
    raw_mrz: list[str] = field(default_factory=list)
    check_digits_valid: bool = False
    optional_data_1: str = ""
    optional_data_2: str = ""


class MRZParser:
    """Detect and parse Machine Readable Zones from documents.

    Supports ICAO 9303 TD1, TD2, and TD3 formats. Can work with either
    raw MRZ text strings or document images (using OpenCV for zone detection).

    Usage:
        parser = MRZParser()

        # From text
        result = parser.parse("P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<\\n"
                              "L898902C36UTO7408122F1204159ZE184226B<<<<<10")

        # From image
        result = parser.parse(document_image)
    """

    def detect_mrz_zone(self, image: np.ndarray) -> np.ndarray | None:
        """Detect the MRZ region in a document image.

        Uses morphological operations to find the dense text block
        typically located at the bottom of identity documents.

        Args:
            image: BGR document image (ideally perspective-corrected).

        Returns:
            Cropped MRZ region as BGR array, or None if not found.
        """
        if image is None or image.size == 0:
            return None

        h, w = image.shape[:2]

        # Focus on the bottom portion of the document where MRZ is located
        bottom_ratio = 0.45
        roi_y = int(h * (1 - bottom_ratio))
        roi = image[roi_y:, :]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Blackhat morphology to reveal dark text on light background
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, rect_kernel)

        # Threshold to get binary mask of text-like regions
        _, thresh = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # Close horizontally to merge MRZ characters into continuous blocks
        close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 5))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_kernel)

        # Erode vertically to remove noise
        erode_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.erode(closed, erode_kernel, iterations=2)
        closed = cv2.dilate(closed, erode_kernel, iterations=2)

        # Find contours of text blocks
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Look for wide, short rectangular contours (MRZ characteristics)
        candidates = []
        roi_h, roi_w = roi.shape[:2]

        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            aspect = cw / ch if ch > 0 else 0

            # MRZ lines are very wide relative to their height
            if aspect > 5 and cw > roi_w * 0.5:
                candidates.append((x, y, cw, ch))

        if not candidates:
            # Fallback: take the widest contour in the bottom region
            contour = max(contours, key=lambda c: cv2.boundingRect(c)[2])
            x, y, cw, ch = cv2.boundingRect(contour)
            if cw < roi_w * 0.3:
                return None
            candidates = [(x, y, cw, ch)]

        # Merge MRZ line candidates into a single bounding box
        min_x = min(c[0] for c in candidates)
        min_y = min(c[1] for c in candidates)
        max_x = max(c[0] + c[2] for c in candidates)
        max_y = max(c[1] + c[3] for c in candidates)

        # Add padding
        pad_x = int((max_x - min_x) * 0.02)
        pad_y = int((max_y - min_y) * 0.15)
        min_x = max(0, min_x - pad_x)
        min_y = max(0, min_y - pad_y)
        max_x = min(roi_w, max_x + pad_x)
        max_y = min(roi_h, max_y + pad_y)

        mrz_crop = roi[min_y:max_y, min_x:max_x]

        if mrz_crop.size == 0:
            return None

        return mrz_crop

    def parse(self, image_or_text: np.ndarray | str) -> MRZResult | None:
        """Parse MRZ from an image or raw text string.

        If given an image, detects the MRZ zone first, then attempts OCR.
        If given a string, parses the MRZ fields directly.

        Args:
            image_or_text: Either a BGR document image or MRZ text string
                           (lines separated by newlines).

        Returns:
            MRZResult with parsed fields, or None if parsing fails.
        """
        if isinstance(image_or_text, str):
            return self._parse_text(image_or_text)

        if isinstance(image_or_text, np.ndarray):
            return self._parse_image(image_or_text)

        return None

    def _parse_image(self, image: np.ndarray) -> MRZResult | None:
        """Extract and parse MRZ from a document image.

        Detects the MRZ zone, then uses OCR to read the text.
        Falls back to direct text detection if doctr is not available.
        """
        mrz_crop = self.detect_mrz_zone(image)
        if mrz_crop is None:
            logger.debug("No MRZ zone detected in image")
            return None

        # Try to OCR the MRZ zone
        try:
            from openbiometrics.document.ocr import DocumentOCR

            ocr = DocumentOCR()
            result = ocr.extract(mrz_crop)
            if result.full_text:
                # Clean up OCR output for MRZ parsing
                mrz_text = _clean_ocr_mrz(result.full_text)
                return self._parse_text(mrz_text)
        except ImportError:
            logger.warning(
                "doctr not installed — cannot OCR the MRZ zone. "
                "Pass MRZ text directly to parse() instead."
            )

        return None

    def _parse_text(self, text: str) -> MRZResult | None:
        """Parse MRZ from raw text lines.

        Supports TD1 (3x30), TD2 (2x36), and TD3 (2x44).
        """
        # Normalize: strip whitespace, split lines, uppercase
        lines = [line.strip().upper() for line in text.strip().splitlines() if line.strip()]

        if not lines:
            return None

        # Determine MRZ type from line count and length
        line_lengths = [len(line) for line in lines]

        if len(lines) == 3 and all(ln == 30 for ln in line_lengths):
            return self._parse_td1(lines)
        elif len(lines) == 2 and all(ln == 36 for ln in line_lengths):
            return self._parse_td2(lines)
        elif len(lines) == 2 and all(ln == 44 for ln in line_lengths):
            return self._parse_td3(lines)

        # Try to detect with tolerance (OCR may introduce length errors)
        if len(lines) == 3 and all(28 <= ln <= 32 for ln in line_lengths):
            # Pad/trim to 30 chars
            lines = [_normalize_line(line, 30) for line in lines]
            return self._parse_td1(lines)
        elif len(lines) == 2:
            avg_len = sum(line_lengths) / 2
            if avg_len >= 42:
                lines = [_normalize_line(line, 44) for line in lines]
                return self._parse_td3(lines)
            elif avg_len >= 34:
                lines = [_normalize_line(line, 36) for line in lines]
                return self._parse_td2(lines)

        logger.debug("Cannot determine MRZ format: %d lines, lengths=%s", len(lines), line_lengths)
        return None

    def _parse_td1(self, lines: list[str]) -> MRZResult:
        """Parse TD1 format: 3 lines x 30 characters (ID cards).

        Line 1: Document type (2) + Issuing state (3) + Document number (9) +
                 Check digit (1) + Optional data 1 (15)
        Line 2: Date of birth (6) + Check digit (1) + Sex (1) +
                 Expiry date (6) + Check digit (1) + Nationality (3) +
                 Optional data 2 (11) + Composite check digit (1)
        Line 3: Name (30)
        """
        l1, l2, l3 = lines

        doc_number = l1[5:14].rstrip("<")
        doc_number_check = l1[14]
        optional_data_1 = l1[15:30].rstrip("<")

        dob = l2[0:6]
        dob_check = l2[6]
        sex = l2[7]
        expiry = l2[8:14]
        expiry_check = l2[14]
        nationality = l2[15:18]
        optional_data_2 = l2[18:29].rstrip("<")
        composite_check = l2[29]

        issuing_country = l1[2:5]
        surname, given_names = _parse_name(l3)

        # Validate check digits
        checks_valid = all([
            _verify_check_digit(l1[5:14], doc_number_check),
            _verify_check_digit(l2[0:6], dob_check),
            _verify_check_digit(l2[8:14], expiry_check),
            _verify_check_digit(
                l1[5:30] + l2[0:7] + l2[8:15] + l2[18:29],
                composite_check,
            ),
        ])

        return MRZResult(
            mrz_type="TD1",
            document_number=doc_number,
            surname=surname,
            given_names=given_names,
            nationality=nationality,
            date_of_birth=dob,
            sex=sex,
            expiry_date=expiry,
            issuing_country=issuing_country,
            raw_mrz=lines,
            check_digits_valid=checks_valid,
            optional_data_1=optional_data_1,
            optional_data_2=optional_data_2,
        )

    def _parse_td2(self, lines: list[str]) -> MRZResult:
        """Parse TD2 format: 2 lines x 36 characters.

        Line 1: Document type (2) + Issuing state (3) + Name (31)
        Line 2: Document number (9) + Check digit (1) + Nationality (3) +
                 Date of birth (6) + Check digit (1) + Sex (1) +
                 Expiry date (6) + Check digit (1) + Optional data (7) +
                 Composite check digit (1)
        """
        l1, l2 = lines

        issuing_country = l1[2:5]
        surname, given_names = _parse_name(l1[5:36])

        doc_number = l2[0:9].rstrip("<")
        doc_number_check = l2[9]
        nationality = l2[10:13]
        dob = l2[13:19]
        dob_check = l2[19]
        sex = l2[20]
        expiry = l2[21:27]
        expiry_check = l2[27]
        optional_data_1 = l2[28:35].rstrip("<")
        composite_check = l2[35]

        checks_valid = all([
            _verify_check_digit(l2[0:9], doc_number_check),
            _verify_check_digit(l2[13:19], dob_check),
            _verify_check_digit(l2[21:27], expiry_check),
            _verify_check_digit(l2[0:10] + l2[13:20] + l2[21:35], composite_check),
        ])

        return MRZResult(
            mrz_type="TD2",
            document_number=doc_number,
            surname=surname,
            given_names=given_names,
            nationality=nationality,
            date_of_birth=dob,
            sex=sex,
            expiry_date=expiry,
            issuing_country=issuing_country,
            raw_mrz=lines,
            check_digits_valid=checks_valid,
            optional_data_1=optional_data_1,
        )

    def _parse_td3(self, lines: list[str]) -> MRZResult:
        """Parse TD3 format: 2 lines x 44 characters (passports).

        Line 1: Document type (2) + Issuing state (3) + Name (39)
        Line 2: Document number (9) + Check digit (1) + Nationality (3) +
                 Date of birth (6) + Check digit (1) + Sex (1) +
                 Expiry date (6) + Check digit (1) + Optional data (14) +
                 Check digit (1) + Composite check digit (1)
        """
        l1, l2 = lines

        issuing_country = l1[2:5]
        surname, given_names = _parse_name(l1[5:44])

        doc_number = l2[0:9].rstrip("<")
        doc_number_check = l2[9]
        nationality = l2[10:13]
        dob = l2[13:19]
        dob_check = l2[19]
        sex = l2[20]
        expiry = l2[21:27]
        expiry_check = l2[27]
        optional_data_1 = l2[28:42].rstrip("<")
        optional_check = l2[42]
        composite_check = l2[43]

        checks_valid = all([
            _verify_check_digit(l2[0:9], doc_number_check),
            _verify_check_digit(l2[13:19], dob_check),
            _verify_check_digit(l2[21:27], expiry_check),
            _verify_check_digit(l2[28:42], optional_check),
            _verify_check_digit(
                l2[0:10] + l2[13:20] + l2[21:43],
                composite_check,
            ),
        ])

        return MRZResult(
            mrz_type="TD3",
            document_number=doc_number,
            surname=surname,
            given_names=given_names,
            nationality=nationality,
            date_of_birth=dob,
            sex=sex,
            expiry_date=expiry,
            issuing_country=issuing_country,
            raw_mrz=lines,
            check_digits_valid=checks_valid,
            optional_data_1=optional_data_1,
        )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _parse_name(name_field: str) -> tuple[str, str]:
    """Parse ICAO name field into surname and given names.

    Names are separated by '<<', components within each part by '<'.

    Returns:
        (surname, given_names) with '<' replaced by spaces and stripped.
    """
    parts = name_field.split("<<", 1)
    surname = parts[0].replace("<", " ").strip()
    given_names = parts[1].replace("<", " ").strip() if len(parts) > 1 else ""
    return surname, given_names


def compute_check_digit(data: str) -> int:
    """Compute ICAO 9303 check digit for a data string.

    Uses the weighting scheme 7, 3, 1 repeating, with character values
    A=10 through Z=35, 0-9 as themselves, and < = 0.

    Args:
        data: String of MRZ characters (uppercase letters, digits, '<').

    Returns:
        Check digit as integer [0-9].
    """
    total = 0
    for i, ch in enumerate(data):
        value = _CHAR_VALUES.get(ch, 0)
        weight = _CHECK_WEIGHTS[i % 3]
        total += value * weight
    return total % 10


def _verify_check_digit(data: str, expected: str) -> bool:
    """Verify an ICAO check digit.

    Args:
        data: The data field to check.
        expected: The expected check digit character.

    Returns:
        True if the computed check digit matches the expected value.
    """
    try:
        expected_val = int(expected)
    except (ValueError, TypeError):
        return False

    return compute_check_digit(data) == expected_val


def _normalize_line(line: str, target_length: int) -> str:
    """Pad or trim an MRZ line to the target length."""
    if len(line) < target_length:
        return line + "<" * (target_length - len(line))
    return line[:target_length]


def _clean_ocr_mrz(text: str) -> str:
    """Clean up OCR output to produce valid MRZ text.

    Common OCR substitutions: O->0, I->1, spaces removed, etc.
    """
    # Replace common OCR misreads in MRZ context
    replacements = {
        " ": "",
        "«": "<",
        "\u00ab": "<",
        "\u00bb": "<",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Keep only valid MRZ characters
    cleaned_lines = []
    for line in text.splitlines():
        cleaned = ""
        for ch in line.upper():
            if ch in _MRZ_CHARS:
                cleaned += ch
        if cleaned:
            cleaned_lines.append(cleaned)

    return "\n".join(cleaned_lines)
