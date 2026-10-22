# Sharath Chandrashekhara — Personal & Academic Portfolio Website

A fast, modular, markdown-driven personal and research website hosted on **GitHub Pages**.

## Overview

This website is designed for effortless maintenance, high-end aesthetics, and zero-dependency compilation:

- **Markdown-Driven Content**: All page content, publications, teaching records, and blog posts are authored in plain Markdown (`.md`) and JSON files located under `content/`.
- **Zero-Dependency Python Compiler**: Built with a lightweight, ultra-fast Python static site generator (`build.py`) requiring only standard Python 3 (no `pip install` or external dependencies required).
- **Automated Modern Design**: Features custom design tokens, responsive typography (`Inter`, `Outfit`, `JetBrains Mono`), dark/light theme switching, interactive BibTeX citation copying, publication filters, and BeerXML recipe inspection.
- **GitHub Pages Ready**: Outputs clean HTML directly for GitHub Pages hosting, with an included GitHub Actions deployment workflow.

---

## Quick Start

### 1. Compile the Website
To compile all markdown content and templates into production HTML pages:
```bash
python3 build.py
```

### 2. Local Preview Server
To launch a local development preview server with live reloading on port `8000`:
```bash
python3 build.py --serve
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

### 3. Clean Build
To remove compiled HTML pages:
```bash
python3 build.py --clean
```

---

## Project Structure

```
sch-home/
├── build.py                  # Zero-dependency Python static site generator & server
├── EDITING_GUIDE.md          # Step-by-step guide for editing content and posts
├── README.md                 # Project documentation
├── .github/workflows/
│   └── deploy.yml            # GitHub Actions CI/CD deployment workflow
├── content/                  # All editable content (Markdown & JSON)
│   ├── site.json             # Global site metadata, contact info, navigation
│   ├── index.md              # Homepage bio, highlights, news items
│   ├── research.md           # Research projects overview
│   ├── publications.json     # Structured publications & patents with bibtex
│   ├── work.md               # Professional experience timeline
│   ├── teaching.md           # Courses taught and guest lecture slides
│   ├── education.md          # Degrees and academic background
│   ├── beer.md               # Small-batch homebrew story & awards
│   ├── recipes.json          # 22 beer recipes dataset
│   └── blog/                 # Markdown blog posts
│       └── welcome.md        # Starter article
├── templates/                # Modular HTML layout templates & partials
│   ├── base.html             # Main HTML5 shell with theme switcher & meta tags
│   ├── components/           # Reusable UI components (navbar, footer, pub_card)
│   ├── home.html             # Homepage template
│   ├── research.html         # Research & publications template
│   ├── work.html             # Work experience template
│   ├── teaching.html         # Teaching template
│   ├── education.html        # Education template
│   ├── beer.html             # Homebrewing lab template
│   ├── recipes.html          # Interactive recipe viewer template
│   ├── blog.html             # Blog archive template
│   └── post.html             # Single blog post template
├── assets/
│   ├── css/
│   │   ├── style.css         # Modern design system (dark/light themes, typography, cards)
│   │   └── beer.css          # Recipe catalog & brewing styles
│   ├── js/
│   │   ├── main.js           # Theme switcher, mobile menu, BibTeX copy toast
│   │   └── beer.js           # Interactive BeerXML parser & search filter
│   ├── files/                # Research PDFs, slides, and CV
│   ├── images/               # Profile photo, UB logo, favicon
│   └── recipes/              # BeerXML recipe files
└── dist/                     # [Auto-generated & git-ignored] Compiled production website
    ├── index.html, research.html, work.html, teaching.html, education.html, recipes.html, beer.html, blog.html
    ├── blog/*.html
    └── assets/               # Bundled assets for deployment
```

---

## How to Edit Content

See the comprehensive [**Content Editing Guide (EDITING_GUIDE.md)**](file:///Users/sharath/Src/sch-home/EDITING_GUIDE.md) for instructions on updating bio, adding papers, writing blog posts, and customizing styles.

---

## License & Credits

- Content: Copyright © Sharath Chandrashekhara.
- Code & Architecture: MIT License.
