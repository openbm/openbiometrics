const BASE = '/api/v1';

// ── Face types ──────────────────────────────────────────────────────────────

export interface FaceDetection {
  bbox: number[];
  confidence: number;
  face_size: number;
  landmarks: number[][];
}

export interface QualityInfo {
  overall_score: number;
  face_size_px: number;
  sharpness: number;
  brightness: number;
  contrast: number;
  head_pose_ok: boolean;
  is_acceptable: boolean;
  reasons: string[];
}

export interface LivenessInfo {
  is_live: boolean | null;
  score: number | null;
}

export interface FaceResponse {
  detection: FaceDetection;
  quality: QualityInfo | null;
  liveness: LivenessInfo | null;
  has_embedding: boolean;
}

export interface DetectResponse {
  faces: FaceResponse[];
  count: number;
}

// ── Document types ──────────────────────────────────────────────────────────

export interface TextLine {
  text: string;
  bbox: number[];
  confidence: number;
}

export interface OCRResult {
  full_text: string;
  lines: TextLine[];
  confidence: number;
}

export interface MRZResult {
  mrz_type: string;
  document_number: string;
  surname: string;
  given_names: string;
  nationality: string;
  date_of_birth: string;
  sex: string;
  expiry_date: string;
  issuing_country: string;
  raw_mrz: string[];
  check_digits_valid: boolean;
}

export interface DocumentScanResponse {
  detected: boolean;
  ocr: OCRResult | null;
  mrz: MRZResult | null;
  has_face: boolean;
}

// ── Verify types ────────────────────────────────────────────────────────────

export interface VerifyResponse {
  is_match: boolean;
  similarity: number;
  face1: FaceResponse | null;
  face2: FaceResponse | null;
}

// ── Liveness types ──────────────────────────────────────────────────────────

export interface Challenge {
  type: string;
  instruction: string;
  timeout_seconds: number;
}

export interface LivenessSessionResponse {
  session_id: string;
  state: 'pending' | 'in_progress' | 'completed' | 'expired';
  challenges: Challenge[];
}

export interface ChallengeResult {
  session_id: string;
  challenge_type: string | null;
  passed: boolean;
  confidence: number;
  challenges_remaining: number;
  session_complete: boolean;
  is_live: boolean | null;
  state: string;
}

// ── API functions ───────────────────────────────────────────────────────────

export async function scanDocument(image: Blob): Promise<DocumentScanResponse> {
  const form = new FormData();
  form.append('image', image, 'document.jpg');
  const res = await fetch(`${BASE}/documents/scan`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function verifyDocument(
  document: Blob,
  selfie: Blob,
  threshold = 0.4,
): Promise<VerifyResponse> {
  const form = new FormData();
  form.append('document', document, 'document.jpg');
  form.append('selfie', selfie, 'selfie.jpg');
  form.append('threshold', String(threshold));
  const res = await fetch(`${BASE}/documents/verify`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function detectFaces(image: Blob): Promise<DetectResponse> {
  const form = new FormData();
  form.append('image', image, 'frame.jpg');
  const res = await fetch(`${BASE}/detect`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createLivenessSession(
  numChallenges = 2,
  timeoutSeconds = 5.0,
): Promise<LivenessSessionResponse> {
  const params = new URLSearchParams({
    num_challenges: String(numChallenges),
    timeout_seconds: String(timeoutSeconds),
  });
  const res = await fetch(`${BASE}/liveness/sessions?${params}`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function submitLivenessFrame(
  sessionId: string,
  image: Blob,
): Promise<ChallengeResult> {
  const form = new FormData();
  form.append('image', image, 'frame.jpg');
  const res = await fetch(`${BASE}/liveness/sessions/${sessionId}/frame`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
