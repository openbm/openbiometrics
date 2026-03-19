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

export interface DemographicsInfo {
  age: number | null;
  gender: 'M' | 'F' | null;
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

export async function detectFaces(image: Blob): Promise<DetectResponse> {
  const form = new FormData();
  form.append('image', image, 'frame.jpg');
  const res = await fetch(`${BASE}/detect`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
