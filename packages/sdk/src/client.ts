import { Faces } from './resources/faces';
import { Watchlists } from './resources/watchlists';
import { Liveness } from './resources/liveness';
import { Documents } from './resources/documents';
import { Video } from './resources/video';
import { Events } from './resources/events';
import { Admin } from './resources/admin';
import type { OpenBiometricsConfig } from './types';

/**
 * OpenBiometrics client.
 *
 * @example
 * ```ts
 * import { OpenBiometrics } from 'openbiometrics';
 *
 * const ob = new OpenBiometrics({ apiKey: 'ob_live_...' });
 *
 * // Detect faces
 * const { faces } = await ob.faces.detect(imageBuffer);
 *
 * // 1:1 verification
 * const { is_match, similarity } = await ob.faces.verify(image1, image2);
 *
 * // Enroll into watchlist
 * await ob.watchlists.enroll(imageBuffer, { label: 'Alice' });
 *
 * // 1:N identification
 * const { matches } = await ob.watchlists.identify(imageBuffer);
 * ```
 */
export class OpenBiometrics {
  readonly faces: Faces;
  readonly watchlists: Watchlists;
  readonly liveness: Liveness;
  readonly documents: Documents;
  readonly video: Video;
  readonly events: Events;
  readonly admin: Admin;

  private readonly apiKey: string;
  private readonly baseUrl: string;

  constructor(config: OpenBiometricsConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = (config.baseUrl ?? 'https://api.openbiometrics.dev').replace(/\/$/, '');

    this.faces = new Faces(this);
    this.watchlists = new Watchlists(this);
    this.liveness = new Liveness(this);
    this.documents = new Documents(this);
    this.video = new Video(this);
    this.events = new Events(this);
    this.admin = new Admin(this);
  }

  /** @internal */
  async request<T>(
    method: string,
    path: string,
    body?: FormData | Record<string, unknown>,
  ): Promise<T> {
    const url = `${this.baseUrl}/api/v1${path}`;
    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.apiKey}`,
    };

    let fetchBody: BodyInit | undefined;

    if (body instanceof FormData) {
      fetchBody = body;
    } else if (body) {
      headers['Content-Type'] = 'application/json';
      fetchBody = JSON.stringify(body);
    }

    const res = await fetch(url, { method, headers, body: fetchBody });

    if (!res.ok) {
      const text = await res.text();
      throw new OpenBiometricsError(res.status, text);
    }

    return res.json() as Promise<T>;
  }

  /** @internal */
  createForm(image: Blob | ArrayBuffer | Uint8Array, fields?: Record<string, string>): FormData {
    const form = new FormData();
    const blob = image instanceof Blob
      ? image
      : new Blob([image as BlobPart]);
    form.append('image', blob, 'image.jpg');
    if (fields) {
      for (const [k, v] of Object.entries(fields)) {
        form.append(k, v);
      }
    }
    return form;
  }
}

export class OpenBiometricsError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: string,
  ) {
    super(`OpenBiometrics API error (${status}): ${body}`);
    this.name = 'OpenBiometricsError';
  }
}
