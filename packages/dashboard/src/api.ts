const BASE = '/api/v1';

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

export interface DemographicsInfo {
  age: number | null;
  gender: string | null;
}

export interface LivenessInfo {
  is_live: boolean | null;
  score: number | null;
}

export interface FaceResponse {
  detection: FaceDetection;
  quality: QualityInfo | null;
  demographics: DemographicsInfo | null;
  liveness: LivenessInfo | null;
  has_embedding: boolean;
}

export interface DetectResponse {
  faces: FaceResponse[];
  count: number;
}

export interface VerifyResponse {
  is_match: boolean;
  similarity: number;
  face1: FaceResponse | null;
  face2: FaceResponse | null;
}

export interface WatchlistMatch {
  identity_id: string;
  label: string;
  similarity: number;
  metadata: Record<string, unknown>;
}

export interface IdentifyResponse {
  face: FaceResponse;
  matches: WatchlistMatch[];
}

export interface HealthResponse {
  status: string;
  models_loaded: boolean;
  watchlist_count: number;
}

export async function detectFaces(image: File): Promise<DetectResponse> {
  const form = new FormData();
  form.append('image', image);
  const res = await fetch(`${BASE}/detect`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function verifyFaces(image1: File, image2: File, threshold = 0.4): Promise<VerifyResponse> {
  const form = new FormData();
  form.append('image1', image1);
  form.append('image2', image2);
  form.append('threshold', String(threshold));
  const res = await fetch(`${BASE}/verify`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function identifyFace(image: File, watchlist = 'default', topK = 5): Promise<IdentifyResponse> {
  const form = new FormData();
  form.append('image', image);
  form.append('watchlist_name', watchlist);
  form.append('top_k', String(topK));
  const res = await fetch(`${BASE}/identify`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function enrollFace(image: File, label: string, watchlist = 'default'): Promise<unknown> {
  const form = new FormData();
  form.append('image', image);
  form.append('label', label);
  form.append('watchlist_name', watchlist);
  const res = await fetch(`${BASE}/watchlist/enroll`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listWatchlists(): Promise<{ watchlists: { name: string; size: number }[] }> {
  const res = await fetch(`${BASE}/watchlist`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// --- Document types ---

export interface TextLine {
  text: string;
  confidence: number;
  bbox: number[];
}

export interface MRZResult {
  raw: string;
  parsed: {
    document_type: string;
    country: string;
    surname: string;
    given_names: string;
    document_number: string;
    nationality: string;
    date_of_birth: string;
    sex: string;
    expiry_date: string;
  };
  valid: boolean;
  check_digits_ok: boolean;
}

export interface OCRResult {
  full_text: string;
  lines: TextLine[];
}

export interface DocumentScanResponse {
  document_type: string;
  mrz: MRZResult | null;
  ocr: OCRResult | null;
  face: FaceResponse | null;
}

// --- Liveness types ---

export interface ChallengeResult {
  challenge: string;
  passed: boolean;
  confidence: number;
}

export interface LivenessSession {
  session_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'expired';
  challenges: string[];
  current_challenge_index: number;
  results: ChallengeResult[];
  is_live: boolean | null;
  created_at: string;
}

// --- Video / Camera types ---

export interface CameraInfo {
  id: string;
  source: string;
  status: CameraStatus;
  fps: number;
  frame_count: number;
  created_at: string;
}

export type CameraStatus = 'running' | 'stopped' | 'error';

// --- Webhook / Events types ---

export interface WebhookInfo {
  id: string;
  url: string;
  event_types: string[];
  secret: string | null;
  created_at: string;
}

export interface EventInfo {
  id: string;
  type: string;
  source: string;
  timestamp: string;
  data: Record<string, unknown>;
}

// --- Admin types ---

export interface ModelStatus {
  name: string;
  size: string;
  status: 'loaded' | 'available' | 'missing';
}

export interface AdminHealth {
  modules: {
    face: { status: string; models_loaded: boolean };
    document: { status: string; models_loaded: boolean };
    liveness: { status: string; sessions_active: number };
    video: { status: string; cameras_active: number };
  };
  system: {
    uptime: string;
    memory_used: string;
    cpu_percent: number;
  };
  config: Record<string, unknown>;
}

// --- Document functions ---

export async function scanDocument(file: File): Promise<DocumentScanResponse> {
  const form = new FormData();
  form.append('image', file);
  const res = await fetch(`${BASE}/document/scan`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function ocrDocument(file: File): Promise<OCRResult> {
  const form = new FormData();
  form.append('image', file);
  const res = await fetch(`${BASE}/document/ocr`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function mrzDocument(file: File): Promise<MRZResult> {
  const form = new FormData();
  form.append('image', file);
  const res = await fetch(`${BASE}/document/mrz`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function verifyDocument(
  docFile: File,
  selfieFile: File,
  threshold = 0.4
): Promise<VerifyResponse> {
  const form = new FormData();
  form.append('document', docFile);
  form.append('selfie', selfieFile);
  form.append('threshold', String(threshold));
  const res = await fetch(`${BASE}/document/verify`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// --- Liveness functions ---

export async function createLivenessSession(numChallenges = 3): Promise<LivenessSession> {
  const res = await fetch(`${BASE}/liveness/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ num_challenges: numChallenges }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function submitLivenessFrame(sessionId: string, file: File): Promise<LivenessSession> {
  const form = new FormData();
  form.append('image', file);
  const res = await fetch(`${BASE}/liveness/session/${sessionId}/frame`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getLivenessSession(sessionId: string): Promise<LivenessSession> {
  const res = await fetch(`${BASE}/liveness/session/${sessionId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteLivenessSession(sessionId: string): Promise<void> {
  const res = await fetch(`${BASE}/liveness/session/${sessionId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
}

// --- Video / Camera functions ---

export async function addCamera(source: string, cameraId?: string): Promise<CameraInfo> {
  const res = await fetch(`${BASE}/video/cameras`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, camera_id: cameraId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function removeCamera(id: string): Promise<void> {
  const res = await fetch(`${BASE}/video/cameras/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
}

export async function listCameras(): Promise<{ cameras: CameraInfo[] }> {
  const res = await fetch(`${BASE}/video/cameras`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function getCameraSnapshotUrl(id: string): string {
  return `${BASE}/video/cameras/${id}/snapshot`;
}

// --- Webhook / Events functions ---

export async function registerWebhook(
  url: string,
  eventTypes: string[],
  secret?: string
): Promise<WebhookInfo> {
  const res = await fetch(`${BASE}/events/webhooks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, event_types: eventTypes, secret }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteWebhook(id: string): Promise<void> {
  const res = await fetch(`${BASE}/events/webhooks/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
}

export async function listWebhooks(): Promise<{ webhooks: WebhookInfo[] }> {
  const res = await fetch(`${BASE}/events/webhooks`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getRecentEvents(
  limit = 50,
  eventType?: string
): Promise<{ events: EventInfo[] }> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (eventType) params.set('event_type', eventType);
  const res = await fetch(`${BASE}/events?${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// --- Admin functions ---

export async function getAdminHealth(): Promise<AdminHealth> {
  const res = await fetch(`${BASE}/admin/health`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getModels(): Promise<{ models: ModelStatus[] }> {
  const res = await fetch(`${BASE}/admin/models`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
