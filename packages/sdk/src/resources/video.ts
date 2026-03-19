import type { OpenBiometrics } from '../client';
import type { CameraConfig, CameraStatus } from '../types';

export class Video {
  constructor(private client: OpenBiometrics) {}

  /**
   * Add a camera source for real-time video processing.
   *
   * @example
   * ```ts
   * const camera = await ob.video.addCamera({
   *   name: 'Lobby',
   *   url: 'rtsp://192.168.1.100/stream',
   *   fps: 5,
   * });
   * ```
   */
  async addCamera(config: { name: string; url: string; fps?: number }): Promise<CameraConfig> {
    return this.client.request<CameraConfig>('POST', '/video/cameras', config);
  }

  /**
   * Remove a camera source.
   */
  async removeCamera(cameraId: string): Promise<void> {
    await this.client.request('DELETE', `/video/cameras/${cameraId}`);
  }

  /**
   * List all configured cameras and their connection status.
   */
  async listCameras(): Promise<CameraStatus[]> {
    return this.client.request<CameraStatus[]>('GET', '/video/cameras');
  }

  /**
   * Get a snapshot from a camera as a binary blob.
   */
  async getSnapshot(cameraId: string): Promise<Blob> {
    const url = `${(this.client as any).baseUrl}/api/v1/video/cameras/${cameraId}/snapshot`;
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${(this.client as any).apiKey}` },
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`OpenBiometrics API error (${res.status}): ${text}`);
    }
    return res.blob();
  }
}
