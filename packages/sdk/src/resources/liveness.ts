import type { OpenBiometrics } from '../client';
import type { Face, LivenessSession, ChallengeType } from '../types';

export class Liveness {
  constructor(private client: OpenBiometrics) {}

  /**
   * Check if a face image is live (real person) or a presentation attack (spoof).
   *
   * @example
   * ```ts
   * const { faces } = await ob.faces.detect(photo);
   * const isLive = faces[0]?.liveness?.is_live;
   * ```
   *
   * Liveness is included in detect() results automatically.
   * This standalone method is for explicit liveness-only checks.
   */
  async check(image: Blob | ArrayBuffer | Uint8Array): Promise<{ face: Face; is_live: boolean; score: number }> {
    const form = this.client.createForm(image);
    const result = await this.client.request<{ faces: Face[] }>('POST', '/detect', form);
    const face = result.faces[0];
    if (!face) throw new Error('No face detected in image');
    return {
      face,
      is_live: face.liveness?.is_live ?? false,
      score: face.liveness?.score ?? 0,
    };
  }

  /**
   * Create an interactive liveness session with challenge-response flow.
   *
   * @example
   * ```ts
   * const session = await ob.liveness.createSession({ challenges: ['blink', 'turn_left'] });
   * console.log(`Session: ${session.session_id}`);
   * ```
   */
  async createSession(options?: {
    challenges?: ChallengeType[];
    ttl_seconds?: number;
  }): Promise<LivenessSession> {
    return this.client.request<LivenessSession>('POST', '/liveness/sessions', options ?? {});
  }

  /**
   * Submit a video frame to an active liveness session.
   */
  async submitFrame(
    sessionId: string,
    frame: Blob | ArrayBuffer | Uint8Array,
  ): Promise<LivenessSession> {
    const form = this.client.createForm(frame, { session_id: sessionId });
    return this.client.request<LivenessSession>('POST', `/liveness/sessions/${sessionId}/frames`, form);
  }

  /**
   * Get the current state of a liveness session.
   */
  async getSession(sessionId: string): Promise<LivenessSession> {
    return this.client.request<LivenessSession>('GET', `/liveness/sessions/${sessionId}`);
  }

  /**
   * Delete / cancel a liveness session.
   */
  async deleteSession(sessionId: string): Promise<void> {
    await this.client.request('DELETE', `/liveness/sessions/${sessionId}`);
  }
}
