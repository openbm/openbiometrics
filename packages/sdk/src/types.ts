export interface FaceDetection {
  bbox: [number, number, number, number];
  confidence: number;
  face_size: number;
  landmarks: [number, number][];
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
  gender: 'M' | 'F' | null;
}

export interface LivenessInfo {
  is_live: boolean | null;
  score: number | null;
}

export interface Face {
  detection: FaceDetection;
  quality: QualityInfo | null;
  demographics: DemographicsInfo | null;
  liveness: LivenessInfo | null;
  has_embedding: boolean;
}

export interface DetectResponse {
  faces: Face[];
  count: number;
}

export interface VerifyResponse {
  is_match: boolean;
  similarity: number;
  face1: Face | null;
  face2: Face | null;
}

export interface WatchlistMatch {
  identity_id: string;
  label: string;
  similarity: number;
  metadata: Record<string, unknown>;
}

export interface IdentifyResponse {
  face: Face;
  matches: WatchlistMatch[];
}

export interface EnrollResponse {
  identity_id: string;
  label: string;
  watchlist: string;
  face: Face;
}

export interface OpenBiometricsConfig {
  apiKey: string;
  baseUrl?: string;
}

// --- Document scanning ---

export interface TextLine {
  text: string;
  confidence: number;
  bbox: [number, number, number, number];
}

export interface OCRResult {
  lines: TextLine[];
  full_text: string;
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
}

export interface DocumentScanResponse {
  document_type: string;
  ocr: OCRResult | null;
  mrz: MRZResult | null;
  face: Face | null;
  confidence: number;
}

// --- Liveness session ---

export type ChallengeType = 'blink' | 'turn_left' | 'turn_right' | 'nod' | 'smile';

export interface ChallengeResult {
  type: ChallengeType;
  passed: boolean;
  score: number;
}

export interface LivenessSession {
  session_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'expired';
  challenges: ChallengeResult[];
  is_live: boolean | null;
  score: number | null;
  created_at: string;
  expires_at: string;
}

// --- Video / camera ---

export interface CameraConfig {
  camera_id: string;
  name: string;
  url: string;
  enabled: boolean;
  fps: number;
}

export interface CameraStatus {
  camera_id: string;
  name: string;
  connected: boolean;
  last_frame_at: string | null;
  fps: number;
}

// --- Webhooks / events ---

export type EventType =
  | 'face.detected'
  | 'face.identified'
  | 'liveness.completed'
  | 'person.detected'
  | 'document.scanned'
  | 'camera.connected'
  | 'camera.disconnected';

export interface WebhookConfig {
  webhook_id: string;
  url: string;
  events: EventType[];
  secret: string;
  active: boolean;
  created_at: string;
}

export interface EventInfo {
  event_id: string;
  type: EventType;
  timestamp: string;
  payload: Record<string, unknown>;
}

// --- Admin ---

export interface ModelStatus {
  name: string;
  loaded: boolean;
  size_mb: number;
  description: string;
}

export interface AdminHealth {
  status: 'ok' | 'degraded' | 'error';
  version: string;
  uptime_seconds: number;
  models: ModelStatus[];
}
