# Pages

This repository hosts a static website built with [Hugo](https://gohugo.io/). The main content is under `page/src`, where all templates, posts and configuration live. The generated static site resides in `docs`. Additional helper scripts and GitHub workflow templates are included.

## Repository structure

```
docs/             # Generated site (HTML/CSS/JS)
memo/             # Miscellaneous notes
page/src/         # Hugo site source
scripts/          # Helper scripts (Node.js, Python, Bash)
workflows/        # Collection of GitHub Actions starter workflows
release.sh        # Simple script to sync generated docs and push
```

## Hugo site (`page/src`)

Key files:

* `config.toml` – main Hugo configuration. Sets base URL, theme and site parameters
* `nav.py` – builds `layouts/partials/nav.html` from `nav.yml` to create a navigation page
* `hugo.sh` – convenience script to regenerate the navigation file and run `hugo`
* `uheader.py` – utility script that scans Markdown posts, uses Baidu NLP APIs to generate metadata (categories, tags, summary) and updates each file’s front matter
* `layouts/`, `static/`, `content/` – standard Hugo directories containing templates, assets and Markdown content.

The Markdown posts under `content/post/` are plain text files.
`search.md` documents the built‑in site search feature and how it relies on the JSON output produced by `layouts/_default/index.json` and `static/js/search.js`.

`nav.yml` defines groups of links used by `nav.py` to build the navigation menu.

## Generated site (`docs`)

The `docs` directory contains the compiled static site and is served via GitHub Pages or another static host. For example `docs/index.html` includes analytics scripts and metadata produced by Hugo.

`release.sh` helps deploy updates by copying `public` output into `docs/` and committing the changes.

## Utility scripts (`scripts/`)

This folder hosts various automation scripts:

* `index.mjs` – Node.js script to interact with Google Search Console and Indexing API. It reads sitemaps, checks indexing status, and can request indexing for pages
* `iptables.sh`, `mongo-export-json.sh`, `uptime-kuma-push.sh` – small Bash utilities (e.g., to update firewall rules)
* `meli-document-input.py` – Python script showing how to import JSON records into MeiliSearch.

A tiny `package.json` lists dependencies for the Node scripts (e.g. `googleapis`, `sitemapper`).

## GitHub workflow templates (`workflows/`)

The large `workflows` directory mirrors GitHub’s [starter-workflows](https://github.com/actions/starter-workflows) repository. It contains numerous example workflows for different languages and frameworks, including Pages deployments like `hugo.yml`. These can serve as references when setting up automated builds.

## Things to explore next

1. **Hugo basics**
   If new to Hugo, skim the official docs on content organization, templates, shortcodes and theming. Inspect the `page/src/themes/hugo.386` folder to see how the theme is structured.
2. **Scripts for automation**
   - Review `scripts/index.mjs` and the helpers in `scripts/shared/` to see how Google APIs are used.
   - Examine Python scripts such as `uheader.py` if interested in content processing or NLP.
3. **Deployment workflow**
   Check how `release.sh` and any CI workflows are used to regenerate `docs` and push changes. This is a simple workflow, but could be extended by adapting templates in `workflows/`.
4. **Search implementation**
   `search.md` and `static/js/search.js` illustrate a client‑side search feature using Fuse.js. Studying these files is useful for customizing search behavior.
5. **Security considerations**
   The `aip` module contains API keys in plain text. Be cautious about committing sensitive credentials.

This repository offers a straightforward Hugo site with supporting automation. Exploring Hugo templates, the helper scripts and the GitHub workflow examples will help you understand how the site is built, deployed and extended.
