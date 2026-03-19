"""Document detection using classical computer vision.

Detects rectangular documents in images using edge detection and contour
analysis. No ML models required — uses OpenCV morphological operations
and perspective correction to extract document crops.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ICAO document size standards (width / height aspect ratios)
_TD1_ASPECT = 1.586  # ID-1 card (credit card size): 85.6 x 53.98 mm
_TD2_ASPECT = 1.415  # ID-2 card: 105 x 74 mm
_TD3_ASPECT = 1.415  # Passport booklet page: 125 x 88 mm
_TD3_MIN_AREA_RATIO = 0.25  # TD3 must occupy at least this fraction of image

_ASPECT_TOLERANCE = 0.15


@dataclass
class DetectedDocument:
    """A document detected in an image.

    Attributes:
        corners: Four corner points of the document in the original image,
                 ordered top-left, top-right, bottom-right, bottom-left.
        document_type: Classified type based on aspect ratio (TD1, TD2, TD3, or unknown).
        confidence: Detection confidence based on contour quality [0, 1].
        warped: Perspective-corrected crop of the document (BGR).
    """

    corners: np.ndarray  # shape (4, 2), float32
    document_type: str
    confidence: float
    warped: np.ndarray


class DocumentDetector:
    """Detect and extract documents from images using classical CV.

    Uses a Canny edge + contour pipeline to locate rectangular regions,
    then applies perspective correction to produce a frontal crop.

    Usage:
        detector = DocumentDetector()
        documents = detector.detect(image)
        if documents:
            cv2.imshow("doc", documents[0].warped)
    """

    def __init__(
        self,
        min_area_ratio: float = 0.05,
        blur_ksize: int = 5,
        canny_low: int = 50,
        canny_high: int = 150,
        epsilon_factor: float = 0.02,
    ):
        """
        Args:
            min_area_ratio: Minimum contour area as a fraction of image area.
            blur_ksize: Gaussian blur kernel size (must be odd).
            canny_low: Canny edge detector low threshold.
            canny_high: Canny edge detector high threshold.
            epsilon_factor: Contour approximation epsilon as a fraction of perimeter.
        """
        self.min_area_ratio = min_area_ratio
        self.blur_ksize = blur_ksize
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.epsilon_factor = epsilon_factor

    def detect(self, image: np.ndarray) -> list[DetectedDocument]:
        """Detect documents in an image.

        Args:
            image: BGR numpy array.

        Returns:
            List of DetectedDocument, sorted by area (largest first).
            Typically returns at most one document.
        """
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]
        image_area = h * w
        min_area = image_area * self.min_area_ratio

        # Preprocessing: grayscale -> blur -> edge detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (self.blur_ksize, self.blur_ksize), 0)
        edges = cv2.Canny(blurred, self.canny_low, self.canny_high)

        # Dilate edges to close gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.dilate(edges, kernel, iterations=1)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Sort by area descending
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        results: list[DetectedDocument] = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                break  # Already sorted, no point continuing

            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, self.epsilon_factor * perimeter, True)

            if len(approx) != 4:
                continue

            # Check convexity
            if not cv2.isContourConvex(approx):
                continue

            corners = approx.reshape(4, 2).astype(np.float32)
            ordered = _order_corners(corners)

            # Compute confidence from contour solidity and area ratio
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0.0
            area_ratio = area / image_area
            confidence = min(1.0, solidity * 0.6 + min(area_ratio / 0.5, 1.0) * 0.4)

            # Perspective correction
            warped = _warp_document(image, ordered)
            if warped is None:
                continue

            doc_type = _classify_document_type(warped, area_ratio)

            results.append(DetectedDocument(
                corners=ordered,
                document_type=doc_type,
                confidence=round(confidence, 3),
                warped=warped,
            ))

        # Sort by area (largest first) — already sorted from contour ordering
        return results


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """Order four points as: top-left, top-right, bottom-right, bottom-left.

    Uses sum and difference of coordinates to determine ordering.
    """
    ordered = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).squeeze()

    ordered[0] = pts[np.argmin(s)]   # top-left: smallest sum
    ordered[2] = pts[np.argmax(s)]   # bottom-right: largest sum
    ordered[1] = pts[np.argmin(d)]   # top-right: smallest difference
    ordered[3] = pts[np.argmax(d)]   # bottom-left: largest difference

    return ordered


def _warp_document(image: np.ndarray, corners: np.ndarray) -> np.ndarray | None:
    """Apply perspective transform to extract a frontal document crop.

    Args:
        image: Source BGR image.
        corners: Ordered corners (TL, TR, BR, BL), shape (4, 2).

    Returns:
        Warped document image, or None if dimensions are invalid.
    """
    tl, tr, br, bl = corners

    # Compute output dimensions
    width_top = float(np.linalg.norm(tr - tl))
    width_bottom = float(np.linalg.norm(br - bl))
    width = int(max(width_top, width_bottom))

    height_left = float(np.linalg.norm(bl - tl))
    height_right = float(np.linalg.norm(br - tr))
    height = int(max(height_left, height_right))

    if width < 10 or height < 10:
        return None

    dst = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1],
    ], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(corners, dst)
    warped = cv2.warpPerspective(image, matrix, (width, height))
    return warped


def _classify_document_type(warped: np.ndarray, area_ratio: float) -> str:
    """Classify document type based on aspect ratio heuristics.

    Args:
        warped: Perspective-corrected document image.
        area_ratio: Document area as fraction of original image area.

    Returns:
        Document type string: "TD1", "TD2", "TD3", or "unknown".
    """
    h, w = warped.shape[:2]
    if h == 0:
        return "unknown"

    aspect = w / h
    # Ensure aspect >= 1 (landscape orientation)
    if aspect < 1.0:
        aspect = 1.0 / aspect

    # TD1 (ID card): aspect ~1.586
    if abs(aspect - _TD1_ASPECT) < _ASPECT_TOLERANCE:
        return "TD1"

    # TD2 and TD3 share similar aspect ratios (~1.415)
    # Distinguish by relative size: TD3 (passport) is physically larger
    if abs(aspect - _TD2_ASPECT) < _ASPECT_TOLERANCE:
        if area_ratio >= _TD3_MIN_AREA_RATIO:
            return "TD3"
        return "TD2"

    return "unknown"
