"""Pydantic models for the REST API."""

from pydantic import BaseModel


# ── Face schemas (existing) ──────────────────────────────────────────────────

class FaceDetection(BaseModel):
    bbox: list[float]  # [x1, y1, x2, y2]
    confidence: float
    face_size: float
    landmarks: list[list[float]]


class QualityInfo(BaseModel):
    overall_score: float
    face_size_px: float
    sharpness: float
    brightness: float
    contrast: float
    head_pose_ok: bool
    is_acceptable: bool
    reasons: list[str]


class DemographicsInfo(BaseModel):
    age: int | None = None
    gender: str | None = None


class LivenessInfo(BaseModel):
    is_live: bool | None = None
    score: float | None = None


class FaceResponse(BaseModel):
    detection: FaceDetection
    quality: QualityInfo | None = None
    demographics: DemographicsInfo | None = None
    liveness: LivenessInfo | None = None
    has_embedding: bool = False


class DetectResponse(BaseModel):
    faces: list[FaceResponse]
    count: int


class VerifyRequest(BaseModel):
    threshold: float = 0.4


class VerifyResponse(BaseModel):
    is_match: bool
    similarity: float
    face1: FaceResponse | None = None
    face2: FaceResponse | None = None


class WatchlistEntry(BaseModel):
    identity_id: str
    label: str
    metadata: dict = {}


class WatchlistSearchResult(BaseModel):
    identity_id: str
    label: str
    similarity: float
    metadata: dict


class IdentifyResponse(BaseModel):
    face: FaceResponse
    matches: list[WatchlistSearchResult]


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    watchlist_count: int


# ── Watchlist deduplication ──────────────────────────────────────────────────

class DuplicateGroupSchema(BaseModel):
    indices: list[int]
    labels: list[str]
    mean_similarity: float


class DeduplicateResponse(BaseModel):
    watchlist: str
    total_entries: int
    duplicate_groups: list[DuplicateGroupSchema]


# ── Document schemas ─────────────────────────────────────────────────────────

class TextLineSchema(BaseModel):
    text: str
    bbox: list[float]
    confidence: float


class OCRResultSchema(BaseModel):
    full_text: str
    lines: list[TextLineSchema] = []
    confidence: float = 0.0


class MRZResultSchema(BaseModel):
    mrz_type: str
    document_number: str
    surname: str
    given_names: str
    nationality: str
    date_of_birth: str
    sex: str
    expiry_date: str
    issuing_country: str
    raw_mrz: list[str] = []
    check_digits_valid: bool = False


class DocumentScanResponse(BaseModel):
    detected: bool
    ocr: OCRResultSchema | None = None
    mrz: MRZResultSchema | None = None
    has_face: bool = False


# ── Liveness schemas ─────────────────────────────────────────────────────────

class ChallengeSchema(BaseModel):
    type: str
    instruction: str
    timeout_seconds: float


class LivenessSessionResponse(BaseModel):
    session_id: str
    state: str
    challenges: list[ChallengeSchema]


class ChallengeResultSchema(BaseModel):
    session_id: str
    challenge_type: str | None = None
    passed: bool
    confidence: float
    challenges_remaining: int
    session_complete: bool
    is_live: bool | None = None
    state: str


# ── Video / Camera schemas ───────────────────────────────────────────────────

class CameraRequest(BaseModel):
    camera_id: str
    source: str  # RTSP URL, file path, or device index as string


class CameraStatusSchema(BaseModel):
    camera_id: str
    source: str
    is_running: bool
    fps: float
    frame_count: int


# ── Event / Webhook schemas ──────────────────────────────────────────────────

class WebhookRequest(BaseModel):
    url: str
    event_types: list[str]
    secret: str | None = None


class WebhookSchema(BaseModel):
    id: str
    url: str
    event_types: list[str]
    created_at: str


class EventSchema(BaseModel):
    id: str
    type: str
    timestamp: str
    source: str
    data: dict = {}
    camera_id: str | None = None


# ── Admin schemas ────────────────────────────────────────────────────────────

class AdminHealthResponse(BaseModel):
    healthy: bool
    modules: dict[str, bool]
    details: dict[str, str]


class ModelStatusSchema(BaseModel):
    name: str
    module: str
    loaded: bool
