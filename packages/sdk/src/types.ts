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
