---
title: Welcome to the New Modular Website
date: "2026-08-21"
tags: ["systems", "meta", "webdev"]
summary: "An introduction to the newly overhauled, markdown-driven architecture powering this website."
---

Welcome to my updated personal and research website!

This site has been completely restructured and modernized into a clean, markdown-driven static architecture designed for rapid content updates and modern web performance.

### Key Highlights of the Architecture

- **Markdown-Driven Content**: All research pages, publications, work experiences, and blog posts are authored in simple Markdown (`.md`) and JSON files located under `content/`.
- **Zero-Dependency Python Compiler**: Running `python3 build.py` instantly builds the entire website in milliseconds using standard Python 3.
- **Automated Modern Styling**: Includes responsive layout grids, dark/light theme switching, interactive BibTeX citations, and live BeerXML recipe inspection.

> [!NOTE]
> To add a new blog post, simply drop a new `.md` file with YAML frontmatter into the `content/blog/` directory and re-run `python3 build.py`!

Stay tuned for more updates on systems research, storage architectures, and small-batch homebrewing experiments.
