"""Document processing endpoints: scan, OCR, MRZ, and document-vs-selfie verification."""

from __future__ import annotations

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.deps import get_kernel
from app.schemas import (
    DocumentScanResponse,
    MRZResultSchema,
    OCRResultSchema,
    TextLineSchema,
    VerifyResponse,
)
from openbiometrics.kernel import BiometricKernel

router = APIRouter()


def _decode_image(file_bytes: bytes) -> np.ndarray:
    """Decode uploaded image bytes to BGR numpy array."""
    arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image")
    return img


def _require_document_module(kernel: BiometricKernel):
    """Raise 503 if the document module is not available."""
    if kernel.document is None:
        raise HTTPException(
            status_code=503,
            detail="Document processing module not available",
        )
    return kernel.document


def _ocr_to_schema(ocr) -> OCRResultSchema:
    """Convert engine OCRResult to API schema."""
    return OCRResultSchema(
        full_text=ocr.full_text,
        lines=[
            TextLineSchema(text=ln.text, bbox=ln.bbox, confidence=ln.confidence)
            for ln in ocr.lines
        ],
        confidence=ocr.confidence,
    )


def _mrz_to_schema(mrz) -> MRZResultSchema:
    """Convert engine MRZResult to API schema."""
    return MRZResultSchema(
        mrz_type=mrz.mrz_type,
        document_number=mrz.document_number,
        surname=mrz.surname,
        given_names=mrz.given_names,
        nationality=mrz.nationality,
        date_of_birth=mrz.date_of_birth,
        sex=mrz.sex,
        expiry_date=mrz.expiry_date,
        issuing_country=mrz.issuing_country,
        raw_mrz=mrz.raw_mrz,
        check_digits_valid=mrz.check_digits_valid,
    )


@router.post("/scan", response_model=DocumentScanResponse)
async def scan_document(
    image: UploadFile = File(...),
    kernel: BiometricKernel = Depends(get_kernel),
):
    """Full document scan: detection + OCR + MRZ parsing."""
    doc_pipeline = _require_document_module(kernel)
    img = _decode_image(await image.read())
    result = doc_pipeline.process(img)

    return DocumentScanResponse(
        detected=result.document is not None,
        ocr=_ocr_to_schema(result.ocr) if result.ocr else None,
        mrz=_mrz_to_schema(result.mrz) if result.mrz else None,
        has_face=result.face is not None,
    )


@router.post("/ocr", response_model=OCRResultSchema)
async def ocr_only(
    image: UploadFile = File(...),
    kernel: BiometricKernel = Depends(get_kernel),
):
    """OCR text extraction only."""
    doc_pipeline = _require_document_module(kernel)
    img = _decode_image(await image.read())

    try:
        from openbiometrics.document.ocr import DocumentOCR
        ocr_engine = DocumentOCR()
        result = ocr_engine.extract(img)
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="OCR engine (python-doctr) not installed",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR failed: {exc}")

    return _ocr_to_schema(result)


@router.post("/mrz", response_model=MRZResultSchema)
async def mrz_only(
    image: UploadFile = File(...),
    kernel: BiometricKernel = Depends(get_kernel),
):
    """MRZ detection and parsing only."""
    _require_document_module(kernel)
    img = _decode_image(await image.read())

    from openbiometrics.document.mrz import MRZParser
    parser = MRZParser()
    result = parser.parse(img)

    if result is None:
        raise HTTPException(status_code=422, detail="No MRZ found in image")

    return _mrz_to_schema(result)


@router.post("/verify", response_model=VerifyResponse)
async def verify_document_vs_selfie(
    document: UploadFile = File(...),
    selfie: UploadFile = File(...),
    threshold: float = Form(0.4),
    kernel: BiometricKernel = Depends(get_kernel),
):
    """Compare the face on a document to a selfie image."""
    doc_pipeline = _require_document_module(kernel)
    face_pipeline = kernel.face
    if face_pipeline is None:
        raise HTTPException(status_code=503, detail="Face pipeline not available")

    doc_img = _decode_image(await document.read())
    selfie_img = _decode_image(await selfie.read())

    # Extract face from document
    doc_result = doc_pipeline.process(doc_img)
    if doc_result.face is None:
        raise HTTPException(status_code=400, detail="No face found on document")

    # Process document face and selfie through face pipeline
    doc_faces = face_pipeline.process(doc_result.face)
    selfie_faces = face_pipeline.process(selfie_img)

    if not doc_faces:
        raise HTTPException(status_code=400, detail="Could not process document face")
    if not selfie_faces:
        raise HTTPException(status_code=400, detail="No face detected in selfie")

    r1, r2 = doc_faces[0], selfie_faces[0]
    if r1.embedding is None or r2.embedding is None:
        raise HTTPException(status_code=500, detail="Recognition model not loaded")

    from openbiometrics.core.recognizer import FaceRecognizer
    from app.routes.faces import _face_to_response

    similarity = FaceRecognizer.compare(r1.embedding, r2.embedding)

    return VerifyResponse(
        is_match=similarity >= threshold,
        similarity=similarity,
        face1=_face_to_response(r1),
        face2=_face_to_response(r2),
    )
