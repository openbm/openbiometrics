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
