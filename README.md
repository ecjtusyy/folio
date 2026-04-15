# folio — GitHub Pages static personal site

Expected Pages URL: `https://ecjtusyy.github.io/folio/`

## Local development

```bash
npm install
npm run dev
```

Open `http://localhost:3000/folio/`.

## Build the static site

```bash
npm ci
npx tsc --noEmit
npm run build
```

The static export is written to `out/`.

## Content maintenance workflow

### Add a new post

1. Create a markdown file in `content/posts/`.
2. Use the file name as the slug.
3. Add `title`, `date`, `slug`, `summary`, and optional `tags` frontmatter.
4. Push to `main`; GitHub Actions publishes automatically.

### Add papers / PDFs / images

- Put static assets under `public/`.
- Use `public/papers/` for PDFs when the papers section is expanded.

## Deployment

GitHub Pages source should be set to **GitHub Actions**. The workflow file is `.github/workflows/deploy-pages.yml`.

## Project site path notes

This repository is a project site. Keep `/folio/` via `basePath: '/folio'`.

## Common problems

- Asset 404 on Pages: verify `basePath: '/folio'`.
- Image export errors: keep `images.unoptimized: true`.
- Dynamic route export errors: every dynamic route must have `generateStaticParams()`.
- Public pages must not use `/api/`, `cookies()`, `headers()`, `draftMode()`, or runtime backend URLs.
