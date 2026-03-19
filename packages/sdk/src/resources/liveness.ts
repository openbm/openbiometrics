import type { OpenBiometrics } from '../client';
import type { Face } from '../types';

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
}
