import type { OpenBiometrics } from '../client';
import type { DetectResponse, VerifyResponse } from '../types';

export class Faces {
  constructor(private client: OpenBiometrics) {}

  /**
   * Detect faces in an image.
   *
   * @example
   * ```ts
   * const { faces, count } = await ob.faces.detect(imageBuffer);
   * for (const face of faces) {
   *   console.log(`Age: ${face.demographics?.age}, Quality: ${face.quality?.overall_score}`);
   * }
   * ```
   */
  async detect(image: Blob | ArrayBuffer | Uint8Array): Promise<DetectResponse> {
    const form = this.client.createForm(image);
    return this.client.request<DetectResponse>('POST', '/detect', form);
  }

  /**
   * 1:1 face verification — check if two images show the same person.
   *
   * @example
   * ```ts
   * const { is_match, similarity } = await ob.faces.verify(photo1, photo2);
   * console.log(is_match ? 'Same person' : 'Different people');
   * ```
   */
  async verify(
    image1: Blob | ArrayBuffer | Uint8Array,
    image2: Blob | ArrayBuffer | Uint8Array,
    options?: { threshold?: number },
  ): Promise<VerifyResponse> {
    const form = new FormData();
    const toBlob = (img: Blob | ArrayBuffer | Uint8Array) =>
      img instanceof Blob ? img : new Blob([img as BlobPart]);
    const blob1 = toBlob(image1);
    const blob2 = toBlob(image2);
    form.append('image1', blob1, 'image1.jpg');
    form.append('image2', blob2, 'image2.jpg');
    if (options?.threshold) {
      form.append('threshold', String(options.threshold));
    }
    return this.client.request<VerifyResponse>('POST', '/verify', form);
  }
}
