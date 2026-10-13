# Planet Hunters Course: study site

A modular online course on how exoplanets are found and how the PlanetHunter tool works. Built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) and [mkdocs-static-i18n](https://github.com/ultrabug/mkdocs-static-i18n). The content follows [docs/STUDY_PLAN.md](../docs/STUDY_PLAN.md).

| Language | Folder | URL path |
|---|---|---|
| English (default) | `docs/en/` | `/` |
| Spanish | `docs/es/` | `/es/` |
| Portuguese | `docs/pt/` | `/pt/` |

Every lesson has the same English file name in the three folders (e.g. `basic/b2-transit-method.md`).

## Run locally

From `study-site/`:

```
uv run --no-project --with-requirements requirements.txt mkdocs serve
```

Open http://127.0.0.1:8000. The page reloads when you edit a file in `docs/`.

Strict build (fails on broken links; same check the deploy runs):

```
uv run --no-project --with-requirements requirements.txt mkdocs build --strict
```

Use `--no-project`: without it, uv picks up the parent PlanetHunter project and tries to reinstall it.

## Publishing: GitHub Pages

The site publishes itself. On every push to `main` that changes anything under `study-site/`, the workflow `.github/workflows/study-site.yml` runs the strict build and deploys to GitHub Pages. A broken link blocks the deploy, so a broken site never goes live.

- URL: https://vitor-92.github.io/planethunter/ (set in `site_url` in `mkdocs.yml`).
- One-time setup: repository **Settings > Pages > Source = GitHub Actions** (the repository must be public for free Pages).
- Custom domain (optional): add a DNS `CNAME` record (e.g. `course.example.com` -> `vitor-92.github.io`), set it in **Settings > Pages > Custom domain**, and update `site_url`.
- Manual run: **Actions > study-site > Run workflow**.

## Editing content

- Lessons: `docs/<lang>/basic/`, `intermediate/`, `advanced/`, `programming/`, `lab/`, plus `index.md`, `how-to-study.md`, `glossary.md`, `references.md`.
- **Add or change a lesson in all three language folders.** A new lesson also goes into the `nav` of `mkdocs.yml`: the top-level `nav` (English) and the `nav` of each language under `plugins > i18n > languages`.
- Writing rules: [STYLE.md](STYLE.md).
- Shared assets: `docs/javascripts/transit-sim.js` (simulator), `docs/javascripts/progress.js` (student progress in localStorage), `docs/css/extra.css`. Both scripts pick their texts from the page language (`<html lang>`).
