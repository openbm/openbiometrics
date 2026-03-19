import type { OpenBiometrics } from '../client';
import type { AdminHealth, ModelStatus } from '../types';

export class Admin {
  constructor(private client: OpenBiometrics) {}

  /**
   * Get server health status including loaded models.
   *
   * @example
   * ```ts
   * const health = await ob.admin.health();
   * console.log(`Status: ${health.status}, Uptime: ${health.uptime_seconds}s`);
   * ```
   */
  async health(): Promise<AdminHealth> {
    return this.client.request<AdminHealth>('GET', '/admin/health');
  }

  /**
   * List all models and their loading status.
   */
  async models(): Promise<ModelStatus[]> {
    return this.client.request<ModelStatus[]>('GET', '/admin/models');
  }

  /**
   * Get or update server configuration.
   */
  async config(updates?: Record<string, unknown>): Promise<Record<string, unknown>> {
    if (updates) {
      return this.client.request<Record<string, unknown>>('PATCH', '/admin/config', updates);
    }
    return this.client.request<Record<string, unknown>>('GET', '/admin/config');
  }
}
