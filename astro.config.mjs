import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://rbraga01.github.io',
  base: '/GlassPlay',
  trailingSlash: 'always',
  output: 'static',
  outDir: process.env.GLASSPLAY_REVIEW === '1' ? './.private/site' : './dist',
  integrations: [sitemap()],
  devToolbar: { enabled: false },
});
