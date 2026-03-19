const BASE = '/api/v1';

export interface FaceDetection {
  bbox: number[];
  confidence: number;
  face_size: number;
  landmarks: number[][];
}

export interface QualityInfo {
  overall_score: number;
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

// Liveness types matching the actual API schemas
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

export async function detectFaces(image: Blob): Promise<DetectResponse> {
  const form = new FormData();
  form.append('image', image, 'frame.jpg');
  const res = await fetch(`${BASE}/detect`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function enrollFace(image: Blob, label: string, watchlist = 'default'): Promise<unknown> {
  const form = new FormData();
  form.append('image', image, 'face.jpg');
  form.append('label', label);
  form.append('watchlist_name', watchlist);
  const res = await fetch(`${BASE}/watchlist/enroll`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function identifyFace(image: Blob, watchlist = 'default', topK = 3): Promise<IdentifyResponse> {
  const form = new FormData();
  form.append('image', image, 'frame.jpg');
  form.append('watchlist_name', watchlist);
  form.append('top_k', String(topK));
  const res = await fetch(`${BASE}/identify`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createLivenessSession(numChallenges = 2, timeoutSeconds = 5.0): Promise<LivenessSessionResponse> {
  const params = new URLSearchParams({
    num_challenges: String(numChallenges),
    timeout_seconds: String(timeoutSeconds),
  });
  const res = await fetch(`${BASE}/liveness/sessions?${params}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function submitLivenessFrame(sessionId: string, image: Blob): Promise<ChallengeResult> {
  const form = new FormData();
  form.append('image', image, 'frame.jpg');
  const res = await fetch(`${BASE}/liveness/sessions/${sessionId}/frame`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getLivenessSession(sessionId: string): Promise<LivenessSessionResponse> {
  const res = await fetch(`${BASE}/liveness/sessions/${sessionId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
