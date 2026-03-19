import type { OpenBiometrics } from '../client';
import type { EnrollResponse, IdentifyResponse } from '../types';

export class Watchlists {
  constructor(private client: OpenBiometrics) {}

  /**
   * Enroll a face into a watchlist.
   *
   * @example
   * ```ts
   * const result = await ob.watchlists.enroll(photo, { label: 'Alice' });
   * console.log(`Enrolled: ${result.identity_id}`);
   * ```
   */
  async enroll(
    image: Blob | ArrayBuffer | Uint8Array,
    options: { label: string; watchlist?: string; identity_id?: string },
  ): Promise<EnrollResponse> {
    const fields: Record<string, string> = { label: options.label };
    if (options.watchlist) fields.watchlist_name = options.watchlist;
    if (options.identity_id) fields.identity_id = options.identity_id;
    const form = this.client.createForm(image, fields);
    return this.client.request<EnrollResponse>('POST', '/watchlist/enroll', form);
  }

  /**
   * 1:N identification — search a face against a watchlist.
   *
   * @example
   * ```ts
   * const { matches } = await ob.watchlists.identify(photo);
   * for (const match of matches) {
   *   console.log(`${match.label}: ${(match.similarity * 100).toFixed(1)}%`);
   * }
   * ```
   */
  async identify(
    image: Blob | ArrayBuffer | Uint8Array,
    options?: { watchlist?: string; topK?: number; threshold?: number },
  ): Promise<IdentifyResponse> {
    const fields: Record<string, string> = {};
    if (options?.watchlist) fields.watchlist_name = options.watchlist;
    if (options?.topK) fields.top_k = String(options.topK);
    if (options?.threshold) fields.threshold = String(options.threshold);
    const form = this.client.createForm(image, fields);
    return this.client.request<IdentifyResponse>('POST', '/identify', form);
  }

  /**
   * Remove an identity from a watchlist.
   */
  async remove(identityId: string, watchlist = 'default'): Promise<void> {
    await this.client.request('DELETE', `/watchlist/${identityId}?watchlist_name=${watchlist}`);
  }

  /**
   * List all watchlists and their sizes.
   */
  async list(): Promise<{ watchlists: { name: string; size: number }[] }> {
    return this.client.request('GET', '/watchlist');
  }
}
