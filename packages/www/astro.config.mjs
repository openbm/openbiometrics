import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import react from '@astrojs/react';

export default defineConfig({
  site: 'https://drinkredwine.github.io',
  base: '/openbiometrics',
  integrations: [
    starlight({
      title: 'OpenBiometrics',
      description: 'Open-source biometric platform for developers',
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/openbiometrics/openbiometrics' },
      ],
      customCss: ['./src/styles/custom.css'],
      sidebar: [
        {
          label: 'Getting Started',
          items: [
            { label: 'Introduction', slug: 'introduction' },
            { label: 'Quickstart', slug: 'quickstart' },
            { label: 'Authentication', slug: 'authentication' },
          ],
        },
        {
          label: 'API Reference',
          items: [
            { label: 'Face Detection', slug: 'api/face-detection' },
            { label: 'Face Verification', slug: 'api/face-verification' },
            { label: 'Passive Liveness', slug: 'api/passive-liveness' },
            { label: 'Active Liveness', slug: 'api/active-liveness' },
            { label: 'Document Processing', slug: 'api/documents' },
            { label: 'Watchlists', slug: 'api/watchlists' },
            { label: 'Person Detection', slug: 'api/person-detection' },
            { label: 'Video Analytics', slug: 'api/video-analytics' },
            { label: 'Events & Webhooks', slug: 'api/events' },
            { label: 'Admin', slug: 'api/admin' },
          ],
        },
        {
          label: 'SDKs',
          items: [
            { label: 'Node.js', slug: 'sdks/nodejs' },
            { label: 'Python', slug: 'sdks/python' },
          ],
        },
        {
          label: 'Architecture',
          items: [
            { label: 'Overview', slug: 'architecture/overview' },
            { label: 'Biometric Kernel', slug: 'architecture/kernel' },
            { label: 'Pipeline System', slug: 'architecture/pipelines' },
          ],
        },
        {
          label: 'Self-Hosting',
          items: [
            { label: 'Docker', slug: 'self-hosting/docker' },
            { label: 'Jetson / Edge', slug: 'self-hosting/edge' },
          ],
        },
      ],
    }),
    react(),
  ],
});
