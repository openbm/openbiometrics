import type { OpenBiometrics } from '../client';
import type { WebhookConfig, EventInfo, EventType } from '../types';

export class Events {
  constructor(private client: OpenBiometrics) {}

  /**
   * Register a webhook to receive event notifications.
   *
   * @example
   * ```ts
   * const webhook = await ob.events.registerWebhook({
   *   url: 'https://example.com/hooks/ob',
   *   events: ['face.identified', 'liveness.completed'],
   * });
   * console.log(`Webhook secret: ${webhook.secret}`);
   * ```
   */
  async registerWebhook(config: {
    url: string;
    events: EventType[];
  }): Promise<WebhookConfig> {
    return this.client.request<WebhookConfig>('POST', '/events/webhooks', config);
  }

  /**
   * Delete a registered webhook.
   */
  async deleteWebhook(webhookId: string): Promise<void> {
    await this.client.request('DELETE', `/events/webhooks/${webhookId}`);
  }

  /**
   * List all registered webhooks.
   */
  async listWebhooks(): Promise<WebhookConfig[]> {
    return this.client.request<WebhookConfig[]>('GET', '/events/webhooks');
  }

  /**
   * Get recent events, optionally filtered by type.
   */
  async getRecent(options?: {
    type?: EventType;
    limit?: number;
  }): Promise<EventInfo[]> {
    const params = new URLSearchParams();
    if (options?.type) params.set('type', options.type);
    if (options?.limit) params.set('limit', String(options.limit));
    const query = params.toString();
    const path = `/events/recent${query ? `?${query}` : ''}`;
    return this.client.request<EventInfo[]>('GET', path);
  }
}
