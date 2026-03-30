import { cpSync, existsSync, mkdirSync, rmSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');

const srcBase = join(root, 'node_modules', 'pdfjs-dist');
const dstBase = join(root, 'public', 'pdfjs');

function resetDir(p) {
  if (existsSync(p)) rmSync(p, { recursive: true, force: true });
  mkdirSync(p, { recursive: true });
}

function copyDir(src, dst) {
  if (!existsSync(src)) throw new Error(`missing ${src}`);
  mkdirSync(dirname(dst), { recursive: true });
  cpSync(src, dst, { recursive: true });
}

try {
  resetDir(dstBase);
  copyDir(join(srcBase, 'build'), join(dstBase, 'build'));
  copyDir(join(srcBase, 'web'), join(dstBase, 'web'));
  // optional assets used by viewer
  if (existsSync(join(srcBase, 'cmaps'))) copyDir(join(srcBase, 'cmaps'), join(dstBase, 'cmaps'));
  if (existsSync(join(srcBase, 'standard_fonts'))) copyDir(join(srcBase, 'standard_fonts'), join(dstBase, 'standard_fonts'));
  console.log('[postinstall] copied pdfjs-dist assets to public/pdfjs');
} catch (e) {
  console.error('[postinstall] failed to copy pdfjs assets:', e);
  process.exit(1);
}
