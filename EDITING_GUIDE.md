# Website Content & Editing Guide

This guide explains how to easily edit, add, and publish content for your website.

All content is maintained in simple, human-readable **Markdown (`.md`)** and **JSON (`.json`)** files in the `content/` folder. Whenever you edit a file, run `python3 build.py` to compile the website into `dist/`.

---

## Quick Reference Commands

| Task | Command |
| :--- | :--- |
| **Compile Site** | `python3 build.py` |
| **Start Live Preview** | `python3 build.py --serve` (open http://localhost:8000) |
| **Clean Build** | `python3 build.py --clean` |

---

## Table of Contents

1. [Editing Bio & Homepage News](#1-editing-bio--homepage-news)
2. [Adding / Updating Publications & Patents](#2-adding--updating-publications--patents)
3. [Updating Work Experience](#3-updating-work-experience)
4. [Updating Teaching & Guest Lectures](#4-updating-teaching--guest-lectures)
5. [Updating Education & Degrees](#5-updating-education--degrees)
6. [Adding a New Blog Post](#6-adding-a-new-blog-post)
7. [Adding / Editing Beer Recipes](#7-adding--editing-beer-recipes)
8. [Updating Site Settings & Contact Info](#8-updating-site-settings--contact-info)

---

## 1. Editing Bio & Homepage News

File: [`content/index.md`](file:///Users/sharath/Src/sch-home/content/index.md)

- **Bio & Dissertation Text**: Edit the Markdown text below the `---` frontmatter delimiter.
- **News Feed**: Add or update entries under `news:` in the frontmatter:

```yaml
news:
  - date: "Aug 2026"
    text: "Announced new research prototype on mobile storage tiering."
  - date: "Nov 2017"
    text: "My dissertation proposal was accepted at UB."
```

---

## 2. Adding / Updating Publications & Patents

File: [`content/publications.json`](file:///Users/sharath/Src/sch-home/content/publications.json)

Add a new JSON object to the array:

```json
{
  "id": "my-new-paper-2026",
  "title": "Novel Storage Architecture for Mobile Platforms",
  "authors": "Sharath Chandrashekhara, Steven Y. Ko",
  "venue": "Proceedings of ACM MobiSys 2026",
  "year": 2026,
  "project": "BlueMountain",
  "badge": "MobiSys '26",
  "pdf": "assets/files/my-paper.pdf",
  "slides": "assets/files/my-slides.pdf",
  "bibtex": "@inproceedings{chandrashekhara2026novel,\n  title={Novel Storage Architecture},\n  author={Chandrashekhara, Sharath and Ko, Steven Y},\n  booktitle={MobiSys},\n  year={2026}\n}"
}
```

*Note: The compiler automatically highlights your name (**Sharath Chandrashekhara**) in bold on the website.*

---

## 3. Updating Work Experience

File: [`content/work.md`](file:///Users/sharath/Src/sch-home/content/work.md)

Add a new company or role under `experience:`:

```yaml
experience:
  - company: "Google"
    role: "Senior Systems Software Engineer"
    location: "Mountain View, CA"
    period: "2018 – Present"
    badge: "Storage Infrastructure"
    summary: "Designing next-generation distributed storage systems."
    highlights:
      - "Led architecture for large-scale persistent storage."
      - "Optimized I/O throughput across heterogeneous storage nodes."
    url: "https://about.google/"
```

---

## 4. Updating Teaching & Guest Lectures

File: [`content/teaching.md`](file:///Users/sharath/Src/sch-home/content/teaching.md)

- **Courses**: Add courses under `courses:` with course code, name, instructor, terms, and description.
- **Guest Lectures**: Add entries under `guest_lectures:` with course title, lecture name, term, and slide URLs.

---

## 5. Updating Education & Degrees

File: [`content/education.md`](file:///Users/sharath/Src/sch-home/content/education.md)

Add or edit degrees under `degrees:` with institution name, degree title, period, location, badge, and bullet details.

---

## 6. Adding a New Blog Post

Directory: [`content/blog/`](file:///Users/sharath/Src/sch-home/content/blog/)

Create a new file, e.g. `content/blog/my-first-post.md`:

```markdown
---
title: Understanding Modern NVMe Flash Architectures
date: "2026-08-25"
tags: ["storage", "flash", "systems"]
summary: "A deep dive into kernel block layers, FTLs, and variable redundancy."
---

Write your markdown post content here!

### Section Heading

You can include code blocks:

```c
int main() {
    printf("Hello Storage Systems!\n");
    return 0;
}
```

And alert callouts:

> [!NOTE]
> This is a helpful callout box.
```

When compiled, this post will automatically appear on [`blog.html`](file:///Users/sharath/Src/sch-home/blog.html) and be published at `blog/my-first-post.html`.

---

## 7. Adding / Editing Beer Recipes

File: [`content/recipes.json`](file:///Users/sharath/Src/sch-home/content/recipes.json)

Add a new recipe entry:

```json
{
  "id": "hazy-ipa",
  "name": "New England Hazy IPA",
  "style": "Hazy / NEIPA",
  "status": "Brewed",
  "description": "Juicy, tropical IPA with double dry-hop of Citra and Mosaic.",
  "xml": "assets/recipes/hazy_ipa.xml",
  "xml_file": "hazy_ipa"
}
```

Drop the `hazy_ipa.xml` BeerXML export file into `assets/recipes/` to enable interactive ingredient viewing and downloads!

---

## 8. Updating Site Settings & Contact Info

File: [`content/site.json`](file:///Users/sharath/Src/sch-home/content/site.json)

Update social media links (LinkedIn, GitHub, Twitter), email address, office location, bio tagline, or navigation bar items.

---

## Publishing Changes to GitHub Pages

1. Edit any `.md` or `.json` file.
2. Compile and test locally:
   ```bash
   python3 build.py --serve
   ```
3. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update publications and blog post"
   git push origin main
   ```
4. GitHub Pages will immediately update!
