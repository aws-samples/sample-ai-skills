import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import {execFileSync} from 'child_process';
import {contentRoot, isLocalDev, sections} from './site';

const siteTitle = '__SITE_TITLE__';

// The navbar version badge. Read from a release tag, not from a tracked file, so
// the badge and the project's version cannot drift apart.
//
// `DOCS_VERSION` wins when set, so a CI job building a release can name the tag
// exactly and read no history. Otherwise it is `git describe` WITHOUT
// `--abbrev=0`: on a tagged commit that is the tag, and past one it is
// `v0.3.0-10-g60189ae`, which names the commit rather than passing it off as the
// release. `--match` keeps a tag that is not a release from becoming the badge.
//
// git runs in this site's own directory and finds the repository from there, so
// no path here counts directory levels up to the repository root.
//
// Returns null rather than throwing when there is no tag to read: a clone need
// not have fetched any, and the badge is decoration. The navbar item below is
// conditional on this value, so the site builds either way.
const projectVersion = (() => {
  if (process.env.DOCS_VERSION) {
    return process.env.DOCS_VERSION.replace(/^v/, '') || null;
  }
  try {
    return execFileSync('git', ['describe', '--tags', '--match', 'v[0-9]*.[0-9]*.[0-9]*'], {
      cwd: __dirname,
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim().replace(/^v/, '') || null;
  } catch {
    return null;
  }
})();

// Setting `exclude` REPLACES Docusaurus's default list rather than adding to it,
// so the defaults are restated here. Without them a `_partial.md`, or a
// `_templates/` directory, would publish as a page.
const defaultExclude = [
  '**/_*.{js,jsx,ts,tsx,md,mdx}',
  '**/_*/**',
  '**/*.test.{js,jsx,ts,tsx}',
  '**/__tests__/**',
];

const config: Config = {
  title: siteTitle,
  future: { v4: true },
  // Where the site is served. The CI job that deploys it knows the host and the
  // base path and supplies them; nothing here names one. A wrong `DOCS_BASE_URL`
  // produces a build whose asset URLs all 404 rather than a build that fails, so
  // check it against the host's actual path.
  url: process.env.DOCS_URL || 'http://localhost:3000',
  baseUrl: process.env.DOCS_BASE_URL || '/',
  // Anchors default to 'warn', which lets a page split ship dead `#anchor` links
  // with a passing build.
  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',
  // `.md` files are CommonMark and `.mdx` files are MDX. Under MDX a bare
  // `<placeholder>` in prose is a JSX tag and breaks the build.
  markdown: { format: 'detect', mermaid: true },
  themes: ['@docusaurus/theme-mermaid'],
  i18n: { defaultLocale: 'en', locales: ['en'] },
  presets: [
    ['classic', {
      docs: {
        path: contentRoot,
        // Pages are served from the site root, with no `/docs/` prefix.
        routeBasePath: '/',
        sidebarPath: './sidebars.ts',
        // Drafts under `working/` are rendered by `pnpm start` and never by a build.
        exclude: isLocalDev ? defaultExclude : [...defaultExclude, 'working/**'],
      },
      blog: false,
      theme: { customCss: './src/css/custom.css' },
    } satisfies Preset.Options],
  ],
  themeConfig: {
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: siteTitle,
      items: [
        // One item per top-level directory of the content root, from the same
        // list sidebars.ts builds its sidebars from: see site.ts.
        ...sections.map(({name, label}) => ({
          type: 'docSidebar' as const,
          sidebarId: name,
          position: 'left' as const,
          label,
        })),
        ...(projectVersion ? [{
          type: 'html' as const,
          position: 'right' as const,
          value: `<span class="navbar-version">v${projectVersion}</span>`,
        }] : []),
      ],
    },
    prism: { theme: prismThemes.github, darkTheme: prismThemes.dracula },
  } satisfies Preset.ThemeConfig,
};

export default config;
