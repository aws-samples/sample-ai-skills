import fs from 'fs';
import path from 'path';

// The authored documentation tree, relative to this site directory. It is the
// one path the site names, and both docusaurus.config.ts and sidebars.ts import
// it from here rather than computing their own copy, so the two cannot disagree
// about where the pages are.
export const contentRoot = path.join(__dirname, '__CONTENT_ROOT__');

// `docusaurus start` is the local development server. Every other command is a
// build, and a build never renders `working/`.
export const isLocalDev = process.argv.includes('start');

export type Section = {name: string; label: string; position: number};

// Docusaurus skips a path whose name starts with `_`, and never reads a dotfile.
const skipped = (name: string) => name.startsWith('_') || name.startsWith('.');

// A directory holding no page would give an empty sidebar, and a navbar item
// naming an empty sidebar fails the build. So a directory of images, or one a
// contributor has created and not yet filled, is left out rather than breaking
// the site.
function hasPages(dir: string): boolean {
  return fs.readdirSync(dir, {withFileTypes: true}).some((entry) => {
    if (skipped(entry.name)) return false;
    if (entry.isDirectory()) return hasPages(path.join(dir, entry.name));
    return /\.mdx?$/.test(entry.name);
  });
}

// `sidebar_label` and `sidebar_position` from a README.md's frontmatter, read one
// line at a time so the site needs no YAML parser. A value this cannot read — a
// multi-line label, say — leaves the section with its directory name and no
// position, never a failed build.
function frontmatter(readme: string): {label?: string; position?: number} {
  if (!fs.existsSync(readme)) return {};
  const block = /^---\r?\n([\s\S]*?)\r?\n---/.exec(fs.readFileSync(readme, 'utf-8'));
  if (!block) return {};
  const label = /^sidebar_label:[ \t]*(.+?)[ \t]*$/m.exec(block[1])?.[1];
  const position = /^sidebar_position:[ \t]*(\d+)[ \t]*$/m.exec(block[1])?.[1];
  return {
    label: label?.replace(/^(['"])(.*)\1$/, '$2'),
    position: position === undefined ? undefined : Number(position),
  };
}

// One section per top-level directory of the content root: each gets its own
// sidebar and its own navbar item, both built from this list. Adding an
// audience or a mode later is therefore a directory with a README.md in it, and
// no configuration edit. A maintainer-only `internal/` directory is served
// exactly when it exists in the tree being built, for the same reason.
//
// The listing runs when the configuration loads, so a directory created while
// `pnpm start` is running appears only after the server restarts.
export const sections: Section[] = fs
  .readdirSync(contentRoot, {withFileTypes: true})
  .filter((entry) => entry.isDirectory() && !skipped(entry.name))
  .filter((entry) => isLocalDev || entry.name !== 'working')
  .filter((entry) => hasPages(path.join(contentRoot, entry.name)))
  .map((entry) => {
    const {label, position} = frontmatter(path.join(contentRoot, entry.name, 'README.md'));
    return {name: entry.name, label: label || entry.name, position: position ?? Infinity};
  })
  .sort((a, b) => a.position - b.position || a.name.localeCompare(b.name));
