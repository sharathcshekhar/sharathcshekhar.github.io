#!/usr/bin/env python3
"""
Static Site Generator for Sharath Chandrashekhara Portfolio (sch-home)
======================================================================
A zero-dependency, ultra-fast static site compiler written in standard Python 3.
Transforms Markdown content and modular templates into modern, accessible HTML
for GitHub Pages.

Usage:
  python3 build.py          # Builds the website in the repository root
  python3 build.py --serve  # Builds and launches local preview server (port 8000)
  python3 build.py --clean  # Cleans generated HTML files
"""

import os
import sys
import json
import re
import html
import time
import shutil
import argparse
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

ROOT_DIR = Path(__file__).parent.resolve()
CONTENT_DIR = ROOT_DIR / "content"
TEMPLATES_DIR = ROOT_DIR / "templates"
ASSETS_DIR = ROOT_DIR / "assets"
DIST_DIR = ROOT_DIR / "dist"
BLOG_CONTENT_DIR = CONTENT_DIR / "blog"
BLOG_OUTPUT_DIR = DIST_DIR / "blog"


# ==============================================================================
# Simple YAML-like Frontmatter & Markdown Parser (Pure Python Standard Library)
# ==============================================================================

def parse_frontmatter(content: str):
    """
    Parses YAML-style frontmatter enclosed in --- at the start of a Markdown file.
    Returns (metadata_dict, markdown_body).
    """
    metadata = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            metadata = parse_yaml_subset(fm_text)

    return metadata, body


def parse_yaml_subset(text: str) -> dict:
    """
    Parses YAML frontmatter respecting indentation levels and nested structures.
    Zero external dependencies.
    """
    lines = [line for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    if not lines:
        return {}
    res = parse_yaml_node(lines)
    return res if isinstance(res, dict) else {}


def get_indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def parse_yaml_value(val: str):
    """Converts string values to Python booleans, integers, floats, or unquoted strings."""
    val = val.strip()
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return val[1:-1].replace(r'\"', '"').replace(r"\'", "'")
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    if val.lower() in ("null", "none", "~"):
        return None
    if val.startswith("[") and val.endswith("]"):
        items = val[1:-1].split(",")
        return [parse_yaml_value(it.strip()) for it in items if it.strip()]
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val


def parse_yaml_node(lines: list):
    if not lines:
        return {}

    first_line = lines[0]
    base_indent = get_indent(first_line)

    # Check if this block is a list or a dict
    is_list = first_line.lstrip().startswith("- ")

    if is_list:
        items = []
        item_chunks = []
        current_chunk = []

        for line in lines:
            indent = get_indent(line)
            stripped = line.strip()

            if indent == base_indent and stripped.startswith("- "):
                if current_chunk:
                    item_chunks.append(current_chunk)
                current_chunk = [line]
            else:
                current_chunk.append(line)

        if current_chunk:
            item_chunks.append(current_chunk)

        for chunk in item_chunks:
            first = chunk[0]
            first_content = first.strip()[2:].strip()
            rest_lines = chunk[1:]

            is_quoted_scalar = (
                (first_content.startswith('"') and first_content.endswith('"') and len(first_content) >= 2)
                or (first_content.startswith("'") and first_content.endswith("'") and len(first_content) >= 2)
            )

            if not is_quoted_scalar and ":" in first_content:
                # Dict item starting on list line, e.g. - company: "Amazon"
                k, v = first_content.split(":", 1)
                k = k.strip()
                v = v.strip()
                dict_lines = []
                if v:
                    dict_lines.append(f"{' ' * (base_indent + 2)}{k}: {v}")
                else:
                    dict_lines.append(f"{' ' * (base_indent + 2)}{k}:")
                dict_lines.extend(rest_lines)
                items.append(parse_yaml_node(dict_lines))
            elif not rest_lines:
                # Simple scalar item, e.g. - "Item 1"
                items.append(parse_yaml_value(first_content))
            else:
                items.append(parse_yaml_value(first_content))

        return items
    else:
        # Mapping (dictionary)
        result = {}
        entry_chunks = []
        current_k = None
        current_v_inline = None
        current_sublines = []

        i = 0
        while i < len(lines):
            line = lines[i]
            indent = get_indent(line)
            stripped = line.strip()

            if indent == base_indent and ":" in stripped and not stripped.startswith("- "):
                if current_k is not None:
                    if current_sublines:
                        result[current_k] = parse_yaml_node(current_sublines)
                    else:
                        result[current_k] = parse_yaml_value(current_v_inline)

                current_k, current_v_inline = stripped.split(":", 1)
                current_k = current_k.strip()
                current_v_inline = current_v_inline.strip()
                current_sublines = []
            else:
                current_sublines.append(line)

            i += 1

        if current_k is not None:
            if current_sublines:
                result[current_k] = parse_yaml_node(current_sublines)
            else:
                result[current_k] = parse_yaml_value(current_v_inline)

        return result


def inline_format(text: str) -> str:
    """
    Formats inline Markdown elements: code, links, images, bold, and italic.
    Protects URLs and HTML tags from regex mangling using non-underscore tokens.
    """
    if not text:
        return ""

    placeholders = []

    def save_placeholder(html_snippet: str) -> str:
        idx = len(placeholders)
        token = f"@@PH{idx}@@"
        placeholders.append(html_snippet)
        return token

    # 1. Protect inline code `code`
    def code_repl(m):
        code_text = html.escape(m.group(1))
        return save_placeholder(f"<code>{code_text}</code>")
    text = re.sub(r'`([^`]+)`', code_repl, text)

    # 2. Protect images ![alt](url)
    def img_repl(m):
        alt, src = m.group(1), m.group(2)
        return save_placeholder(f'<img src="{src}" alt="{alt}" loading="lazy">')
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', img_repl, text)

    # 3. Protect links [text](url)
    def link_repl(m):
        label, url = m.group(1), m.group(2)
        target = ' target="_blank" rel="noopener"' if url.startswith("http") else ''
        return save_placeholder(f'<a href="{url}"{target}>{label}</a>')
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_repl, text)

    # 4. Bold + Italic: ***text***
    text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'<strong><em>\1</em></strong>', text)

    # 5. Bold: **text** or __text__
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)

    # 6. Italic: *text* or _text_ (only whole-word or delimited)
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', r'<em>\1</em>', text)

    # 7. Restore placeholders
    for idx, snippet in enumerate(placeholders):
        text = text.replace(f"@@PH{idx}@@", snippet)

    return text


def markdown_to_html(md_text: str) -> str:
    """
    Transforms Markdown text into semantic HTML5.
    Supports headings, bold, italic, links, images, blockquotes, alerts,
    tables, code blocks, and lists.
    """
    if not md_text:
        return ""

    lines = md_text.splitlines()
    html_lines = []
    in_code_block = False
    code_lang = ""
    code_content = []
    in_list = False
    list_type = "ul"
    in_table = False
    table_rows = []

    def close_list():
        nonlocal in_list, list_type
        if in_list:
            html_lines.append(f"</{list_type}>")
            in_list = False

    def close_table():
        nonlocal in_table, table_rows
        if in_table and table_rows:
            html_lines.append('<div class="table-responsive"><table class="markdown-table">')
            for r_idx, row in enumerate(table_rows):
                cols = [c.strip() for c in row.split("|")[1:-1]]
                if r_idx == 0:
                    html_lines.append("<thead><tr>" + "".join(f"<th>{inline_format(c)}</th>" for c in cols) + "</tr></thead><tbody>")
                elif r_idx == 1 and all(set(c).issubset({"-", ":", " "}) for c in cols):
                    continue  # Table delimiter line
                else:
                    html_lines.append("<tr>" + "".join(f"<td>{inline_format(c)}</td>" for c in cols) + "</tr>")
            html_lines.append("</tbody></table></div>")
            table_rows = []
            in_table = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Code Block Toggle
        if stripped.startswith("```"):
            close_list()
            close_table()
            if in_code_block:
                escaped_code = html.escape("\n".join(code_content))
                html_lines.append(f'<pre><code class="language-{code_lang}">{escaped_code}</code></pre>')
                in_code_block = False
                code_content = []
            else:
                in_code_block = True
                code_lang = stripped[3:].strip()
            i += 1
            continue

        if in_code_block:
            code_content.append(line)
            i += 1
            continue

        # Blank Line
        if not stripped:
            close_list()
            close_table()
            i += 1
            continue

        # Tables
        if stripped.startswith("|") and stripped.endswith("|"):
            close_list()
            in_table = True
            table_rows.append(stripped)
            i += 1
            continue
        elif in_table:
            close_table()

        # Horizontal Rule
        if stripped in ("---", "***", "___"):
            close_list()
            html_lines.append("<hr>")
            i += 1
            continue

        # GitHub Alert Boxes (e.g. > [!NOTE])
        if stripped.startswith("> [!"):
            close_list()
            alert_type = stripped[4:].split("]")[0].lower()
            alert_lines = []
            i += 1
            while i < len(lines) and lines[i].strip().startswith(">"):
                alert_lines.append(lines[i].strip()[1:].strip())
                i += 1
            alert_body = inline_format(" ".join(alert_lines))
            html_lines.append(f'<div class="alert-box alert-{alert_type}"><strong>{alert_type.upper()}:</strong> {alert_body}</div>')
            continue

        # Blockquote
        if stripped.startswith(">"):
            close_list()
            quote_text = stripped[1:].strip()
            html_lines.append(f"<blockquote><p>{inline_format(quote_text)}</p></blockquote>")
            i += 1
            continue

        # Headings
        if stripped.startswith("#"):
            close_list()
            level = len(stripped) - len(stripped.lstrip("#"))
            heading_text = stripped[level:].strip()
            slug = re.sub(r"[^a-zA-Z0-9]+", "-", heading_text.lower()).strip("-")
            html_lines.append(f'<h{level} id="{slug}">{inline_format(heading_text)}</h{level}>')
            i += 1
            continue

        # Unordered Lists
        if stripped.startswith(("- ", "* ", "+ ")):
            if not in_list or list_type != "ul":
                close_list()
                in_list = True
                list_type = "ul"
                html_lines.append("<ul>")
            item_text = stripped[2:].strip()
            html_lines.append(f"<li>{inline_format(item_text)}</li>")
            i += 1
            continue

        # Ordered Lists
        match_ol = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if match_ol:
            if not in_list or list_type != "ol":
                close_list()
                in_list = True
                list_type = "ol"
                html_lines.append("<ol>")
            item_text = match_ol.group(2).strip()
            html_lines.append(f"<li>{inline_format(item_text)}</li>")
            i += 1
            continue

        close_list()

        # Regular Paragraph
        html_lines.append(f"<p>{inline_format(stripped)}</p>")
        i += 1

    close_list()
    close_table()

    return "\n".join(html_lines)


# ==============================================================================
# Modular Template Engine (Zero Dependencies)
# ==============================================================================

class TemplateRenderer:
    """
    Lightweight, modular template renderer supporting:
    - {% include "file.html" %}
    - {{ variable }} & {{ variable | safe }} & {{ variable | escape }}
    - {% if condition %} ... {% else %} ... {% endif %}
    - {% for item in collection %} ... {% endfor %}
    """

    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.cache = {}

    def get_template(self, name: str) -> str:
        if name not in self.cache:
            path = self.templates_dir / name
            if not path.exists():
                raise FileNotFoundError(f"Template not found: {path}")
            self.cache[name] = path.read_text(encoding="utf-8")
        return self.cache[name]

    def render(self, template_name: str, context: dict) -> str:
        raw = self.get_template(template_name)
        # Step 1: Resolve all includes
        resolved = self._resolve_includes(raw)
        # Step 2: Render logic and variables
        return self._render_string(resolved, context)

    def _resolve_includes(self, text: str, depth: int = 0) -> str:
        if depth > 10:
            return text

        pattern = re.compile(r'\{%\s*include\s+["\']([^"\']+)["\']\s*%\}')

        def repl(match):
            inc_name = match.group(1)
            inc_content = self.get_template(inc_name)
            return self._resolve_includes(inc_content, depth + 1)

        return pattern.sub(repl, text)

    def _render_string(self, text: str, context: dict) -> str:
        tokens = self._tokenize(text)
        rendered, _ = self._parse_block(tokens, context, stop_at=set())
        return rendered

    def _tokenize(self, text: str) -> list:
        pattern = re.compile(r'(\{%.*?%\}|\{\{.*?\}\})', re.DOTALL)
        parts = pattern.split(text)
        return [p for p in parts if p]

    def _parse_block(self, tokens: list, context: dict, stop_at: set) -> tuple:
        out = []
        idx = 0

        while idx < len(tokens):
            tok = tokens[idx]

            if tok.startswith("{%") and tok.endswith("%}"):
                tag_content = tok[2:-2].strip()
                tag_parts = tag_content.split()
                tag_name = tag_parts[0] if tag_parts else ""

                if tag_name in stop_at:
                    return "".join(out), idx

                if tag_name == "if":
                    condition_str = " ".join(tag_parts[1:])
                    # Collect branches: if_body, optional else_body
                    idx += 1
                    if_tokens = []
                    else_tokens = []
                    current_branch = if_tokens
                    nested_ifs = 0

                    while idx < len(tokens):
                        sub_tok = tokens[idx]
                        if sub_tok.startswith("{%") and sub_tok.endswith("%}"):
                            sub_tag = sub_tok[2:-2].strip().split()
                            sub_name = sub_tag[0] if sub_tag else ""
                            if sub_name == "if":
                                nested_ifs += 1
                            elif sub_name == "endif":
                                if nested_ifs > 0:
                                    nested_ifs -= 1
                                else:
                                    break
                            elif sub_name == "else" and nested_ifs == 0:
                                current_branch = else_tokens
                                idx += 1
                                continue
                        current_branch.append(sub_tok)
                        idx += 1

                    cond_result = self._eval_condition(condition_str, context)
                    branch_to_render = if_tokens if cond_result else else_tokens
                    sub_out, _ = self._parse_block(branch_to_render, context, stop_at=set())
                    out.append(sub_out)

                elif tag_name == "for":
                    # {% for item in collection %}
                    var_name = tag_parts[1]
                    collection_name = tag_parts[3]
                    idx += 1
                    for_tokens = []
                    nested_fors = 0

                    while idx < len(tokens):
                        sub_tok = tokens[idx]
                        if sub_tok.startswith("{%") and sub_tok.endswith("%}"):
                            sub_tag = sub_tok[2:-2].strip().split()
                            sub_name = sub_tag[0] if sub_tag else ""
                            if sub_name == "for":
                                nested_fors += 1
                            elif sub_name == "endfor":
                                if nested_fors > 0:
                                    nested_fors -= 1
                                else:
                                    break
                        for_tokens.append(sub_tok)
                        idx += 1

                    collection = self._resolve_var(collection_name, context) or []
                    if isinstance(collection, dict):
                        collection = list(collection.values())

                    for item in collection:
                        sub_ctx = dict(context)
                        sub_ctx[var_name] = item
                        sub_out, _ = self._parse_block(list(for_tokens), sub_ctx, stop_at=set())
                        out.append(sub_out)

            elif tok.startswith("{{") and tok.endswith("}}"):
                expr = tok[2:-2].strip()
                val = self._eval_expr(expr, context)
                out.append(str(val if val is not None else ""))
            else:
                out.append(tok)

            idx += 1

        return "".join(out), idx

    def _resolve_var(self, name: str, context: dict):
        parts = name.split(".")
        val = context
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            elif hasattr(val, p):
                val = getattr(val, p)
            else:
                return None
        return val

    def _eval_expr(self, expr: str, context: dict):
        filters = [f.strip() for f in expr.split("|")]
        var_name = filters[0]
        val = self._resolve_var(var_name, context)

        for flt in filters[1:]:
            if flt == "safe":
                pass
            elif flt == "escape":
                val = html.escape(str(val or ""))
            elif flt.startswith("default:"):
                def_val = flt.split(":", 1)[1].strip()
                if not val:
                    val = self._resolve_var(def_val, context) or def_val
        return val

    def _eval_condition(self, cond: str, context: dict) -> bool:
        cond = cond.strip()
        if " == " in cond:
            left, right = cond.split(" == ", 1)
            left_val = self._resolve_var_or_literal(left.strip(), context)
            right_val = self._resolve_var_or_literal(right.strip(), context)
            return left_val == right_val
        elif " != " in cond:
            left, right = cond.split(" != ", 1)
            left_val = self._resolve_var_or_literal(left.strip(), context)
            right_val = self._resolve_var_or_literal(right.strip(), context)
            return left_val != right_val
        elif " or " in cond:
            parts = cond.split(" or ")
            return any(self._eval_condition(p, context) for p in parts)
        elif " and " in cond:
            parts = cond.split(" and ")
            return all(self._eval_condition(p, context) for p in parts)
        else:
            val = self._resolve_var(cond, context)
            return bool(val)

    def _resolve_var_or_literal(self, term: str, context: dict):
        if (term.startswith('"') and term.endswith('"')) or (term.startswith("'") and term.endswith("'")):
            return term[1:-1]
        return self._resolve_var(term, context)


# ==============================================================================
# Site Builder Pipeline
# ==============================================================================

def build_site(output_dir: Path = DIST_DIR):
    """Compiles all markdown files, data files, and templates into static HTML."""
    start_time = time.time()
    print("🔨 Starting sch-home static build...")

    # Ensure output directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    blog_out_dir = output_dir / "blog"
    blog_out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy static assets to output directory
    dist_assets = output_dir / "assets"
    if ASSETS_DIR.exists():
        if dist_assets.exists():
            shutil.rmtree(dist_assets)
        shutil.copytree(ASSETS_DIR, dist_assets)
        print("  ✓ Copied assets/ -> dist/assets/")

    # 2. Add .nojekyll for GitHub Pages
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    renderer = TemplateRenderer(TEMPLATES_DIR)

    # 3. Load global site metadata
    site_meta_path = CONTENT_DIR / "site.json"
    site = {}
    if site_meta_path.exists():
        site = json.loads(site_meta_path.read_text(encoding="utf-8"))

    # Support injecting contact email from environment (e.g. GitHub Secret EMAIL or SITE_EMAIL)
    env_email = os.environ.get("EMAIL", "").strip() or os.environ.get("SITE_EMAIL", "").strip()
    if env_email:
        site["email"] = env_email
        if "social" in site and isinstance(site["social"], dict):
            site["social"]["email"] = f"mailto:{env_email}"
    else:
        site["email"] = site.get("email", "").strip()
        if not site["email"]:
            if "social" in site and isinstance(site["social"], dict):
                site["social"]["email"] = ""

    # 4. Load publications data
    pub_path = CONTENT_DIR / "publications.json"
    if pub_path.exists():
        pubs = json.loads(pub_path.read_text(encoding="utf-8"))
        for p in pubs:
            if "authors" in p:
                authors_html = p["authors"].replace(
                    "Sharath Chandrashekhara", "<strong>Sharath Chandrashekhara</strong>"
                )
                authors_html = authors_html.replace(
                    "Steven Y. Ko", '<a href="https://steveyko.github.io/teaching/" target="_blank" rel="noopener">Steven Y. Ko</a>'
                ).replace(
                    "Steve Ko", '<a href="https://steveyko.github.io/teaching/" target="_blank" rel="noopener">Steve Ko</a>'
                ).replace(
                    "Karthik Dantu", '<a href="https://dkkarthik.github.io/" target="_blank" rel="noopener">Karthik Dantu</a>'
                ).replace(
                    "Vipin Chaudhary", '<a href="https://case.edu/engineering/about/faculty-and-staff-directory/vipin-chaudhary" target="_blank" rel="noopener">Vipin Chaudhary</a>'
                )
                p["authors_html"] = authors_html
        site["publications"] = pubs
        site["publications_count"] = len(site["publications"])

    # 5. Load recipes data
    rec_path = CONTENT_DIR / "recipes.json"
    if rec_path.exists():
        site["recipes"] = json.loads(rec_path.read_text(encoding="utf-8"))
        site["recipes_count"] = len(site["recipes"])

    # 6. Parse and build blog posts
    posts = []
    if BLOG_CONTENT_DIR.exists():
        for md_file in BLOG_CONTENT_DIR.glob("*.md"):
            post_raw = md_file.read_text(encoding="utf-8")
            post_meta, post_body = parse_frontmatter(post_raw)
            post_html = markdown_to_html(post_body)
            word_count = len(post_body.split())
            reading_time = max(1, round(word_count / 200))

            slug = md_file.stem
            post_data = {
                **post_meta,
                "id": slug,
                "slug": slug,
                "url": f"blog/{slug}.html",
                "root": "../",
                "body_html": post_html,
                "reading_time": reading_time,
                "date": str(post_meta.get("date", "2026-08-21")),
            }
            posts.append(post_data)

            # Render individual post page
            post_context = {"site": site, "page": post_data}
            post_page_content = renderer.render("post.html", post_context)
            final_post_html = renderer.render("base.html", {
                "site": site,
                "page": post_data,
                "content": post_page_content
            })

            out_post_file = blog_out_dir / f"{slug}.html"
            out_post_file.write_text(final_post_html, encoding="utf-8")
            print(f"  ✓ Compiled post: {out_post_file.relative_to(ROOT_DIR)}")

    posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    site["posts"] = posts

    # 5. Core pages mapping: (content_file, layout_template, output_html_filename, page_id)
    pages = [
        ("index.md", "home.html", "index.html", "home"),
        ("research.md", "research.html", "research.html", "research"),
        ("work.md", "work.html", "work.html", "work"),
        ("teaching.md", "teaching.html", "teaching.html", "teaching"),
        ("education.md", "education.html", "education.html", "education"),
        ("beer.md", "beer.html", "beer.html", "beer"),
    ]

    for md_name, layout_name, out_name, page_id in pages:
        md_path = CONTENT_DIR / md_name
        if not md_path.exists():
            continue

        raw_md = md_path.read_text(encoding="utf-8")
        page_meta, page_body = parse_frontmatter(raw_md)
        body_html = markdown_to_html(page_body)

        page_data = {
            **page_meta,
            "id": page_id,
            "root": "",
            "body_html": body_html,
            "title": page_meta.get("title", page_id.capitalize()),
        }

        if "news" in page_data and isinstance(page_data["news"], list):
            formatted_news = []
            for n in page_data["news"]:
                if isinstance(n, dict):
                    n_copy = dict(n)
                    if "text" in n_copy:
                        n_copy["text"] = inline_format(n_copy["text"])
                    formatted_news.append(n_copy)
                else:
                    formatted_news.append(n)
            page_data["news"] = formatted_news

        context = {"site": site, "page": page_data}
        inner_content = renderer.render(layout_name, context)
        full_page_html = renderer.render("base.html", {
            "site": site,
            "page": page_data,
            "content": inner_content
        })

        out_file = output_dir / out_name
        out_file.write_text(full_page_html, encoding="utf-8")
        print(f"  ✓ Compiled page: {out_name}")

    # 6. Render recipes catalog page
    recipes_page_data = {
        "id": "recipes",
        "root": "",
        "title": "Beer Recipes - Homebrewing Lab",
        "description": "Small-batch homebrew recipes and BeerXML files for ales, stouts, IPAs, and Belgian beers."
    }
    recipes_inner = renderer.render("recipes.html", {"site": site, "page": recipes_page_data})
    recipes_html = renderer.render("base.html", {
        "site": site,
        "page": recipes_page_data,
        "content": recipes_inner
    })
    (output_dir / "recipes.html").write_text(recipes_html, encoding="utf-8")
    print("  ✓ Compiled page: recipes.html")

    # 7. Render blog archive page
    blog_page_data = {
        "id": "blog",
        "root": "",
        "title": "Blog & Articles",
        "description": "Articles on systems engineering, storage architectures, and homebrewing."
    }
    blog_inner = renderer.render("blog.html", {"site": site, "page": blog_page_data})
    blog_html = renderer.render("base.html", {
        "site": site,
        "page": blog_page_data,
        "content": blog_inner
    })
    (output_dir / "blog.html").write_text(blog_html, encoding="utf-8")
    print("  ✓ Compiled page: blog.html")

    elapsed = time.time() - start_time
    print(f"✨ Build finished successfully in {elapsed:.3f}s!")


def clean_site():
    """Removes compiled dist directory and any legacy root HTML pages."""
    print("🧹 Cleaning generated HTML files...")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        print(f"  Deleted dist/ directory")

    # Clean legacy root HTML pages if any exist
    legacy_files = [
        "index.html", "research.html", "work.html", "teaching.html",
        "education.html", "beer.html", "recipes.html", "blog.html", "redirect.html"
    ]
    for f in legacy_files:
        p = ROOT_DIR / f
        if p.exists():
            p.unlink()
            print(f"  Deleted legacy root {f}")

    legacy_blog = ROOT_DIR / "blog"
    if legacy_blog.exists():
        shutil.rmtree(legacy_blog)
        print("  Deleted legacy root blog/ directory")


def serve_site(port: int = 8000):
    """Runs a local preview server serving dist/ with live rebuilding."""
    build_site(DIST_DIR)
    os.chdir(DIST_DIR)

    class CustomHandler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            super().end_headers()

    with socketserver.TCPServer(("", port), CustomHandler) as httpd:
        print(f"\n🚀 Server running at http://localhost:{port}/")
        print("📁 Serving folder: dist/")
        print("💡 Press Ctrl+C to stop the preview server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")


def main():
    parser = argparse.ArgumentParser(description="Sharath Chandrashekhara Portfolio Static Site Compiler")
    parser.add_argument("-s", "--serve", action="store_true", help="Launch local preview server")
    parser.add_argument("-c", "--clean", action="store_true", help="Clean generated HTML files")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port for preview server (default: 8000)")

    args = parser.parse_args()

    if args.clean:
        clean_site()
    elif args.serve:
        serve_site(port=args.port)
    else:
        build_site()


if __name__ == "__main__":
    main()
