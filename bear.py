#!/usr/bin/env python3
"""
Tiny Blog - Self-hosted minimal blog generator
Inspired by bearblog.dev
"""

import os
import re
import http.server
import socketserver
import argparse
from datetime import datetime
from pathlib import Path

# Configuration
POSTS_DIR = "posts"
OUTPUT_DIR = "public"
BLOG_TITLE = "My Blog"
BLOG_SUBTITLE = "A minimal, no-nonsense blog"

# CSS (based on Bear Blog style)
CSS = """
:root {
    --width: 720px;
    --font-main: Verdana, sans-serif;
    --font-secondary: Verdana, sans-serif;
    --font-scale: 1em;
    --background-color: #fff;
    --heading-color: #222;
    --text-color: #444;
    --link-color: #3273dc;
    --visited-color: #8b6fcb;
    --code-background-color: #f2f2f2;
    --code-color: #222;
    --blockquote-color: #222;
}

@media (prefers-color-scheme: dark) {
    :root {
        --background-color: #01242e;
        --heading-color: #eee;
        --text-color: #ddd;
        --link-color: #8cc2dd;
        --visited-color: #8b6fcb;
        --code-background-color: #000;
        --code-color: #ddd;
        --blockquote-color: #ccc;
    }
}

body {
    font-family: var(--font-secondary);
    font-size: var(--font-scale);
    margin: auto;
    padding: 20px;
    max-width: var(--width);
    text-align: left;
    background-color: var(--background-color);
    word-wrap: break-word;
    overflow-wrap: break-word;
    line-height: 1.5;
    color: var(--text-color);
}

h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-main);
    color: var(--heading-color);
}

a {
    color: var(--link-color);
    cursor: pointer;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

a:visited {
    color: var(--visited-color);
}

nav a {
    margin-right: 10px;
}

strong, b {
    color: var(--heading-color);
}

main {
    line-height: 1.6;
}

hr {
    border: 0;
    border-top: 1px dashed;
}

img {
    max-width: 100%;
}

code {
    font-family: monospace;
    padding: 2px 4px;
    background-color: var(--code-background-color);
    color: var(--code-color);
    border-radius: 3px;
}

pre {
    background-color: var(--code-background-color);
    padding: 1em;
    border-radius: 3px;
    overflow-x: auto;
}

pre code {
    padding: 0;
    background: none;
}

blockquote {
    border-left: 3px solid #999;
    color: var(--blockquote-color);
    padding-left: 20px;
    margin-left: 0;
    font-style: italic;
}

footer {
    padding: 25px 0;
    text-align: center;
    color: #777;
    font-size: 0.9em;
}

.title {
    display: inline-block;
}

.title:hover {
    text-decoration: none;
}

.title h1 {
    font-size: 1.5em;
    margin-bottom: 0;
}

.logo {
    font-family: "Menlo", monospace;
}

/* Post list */
ul.blog-posts {
    list-style-type: none;
    padding: 0;
}

ul.blog-posts li {
    display: flex;
    margin-bottom: 10px;
}

ul.blog-posts li span {
    flex: 0 0 130px;
    font-family: monospace;
    font-size: 14px;
    color: #777;
}

ul.blog-posts li a:visited {
    color: var(--visited-color);
}

/* Article */
article {
    margin-top: 20px;
}

article header {
    margin-bottom: 30px;
}

article header h1 {
    margin-bottom: 5px;
}

article header time {
    font-family: monospace;
    font-size: 14px;
    color: #777;
}

.back-link {
    margin-top: 30px;
    display: block;
}

mark {
    background-color: #fff3cd;
    padding: 2px 4px;
    border-radius: 3px;
}

@media (prefers-color-scheme: dark) {
    mark {
        background-color: #664d03;
        color: #fff3cd;
    }
}
"""

# Simple Markdown parser (no external dependencies)
def parse_markdown(text):
    """Convert basic Markdown to HTML"""
    lines = text.split('\n')
    html_lines = []
    in_code_block = False
    in_ul = False
    in_ol = False
    in_blockquote = False
    blockquote_lines = []
    
    for line in lines:
        # Code blocks
        if line.startswith('```'):
            if in_code_block:
                html_lines.append('</code></pre>')
                in_code_block = False
            else:
                html_lines.append('<pre><code>')
                in_code_block = True
            continue
        
        if in_code_block:
            html_lines.append(escape_html(line))
            continue
        
        # Close lists if needed
        if in_ul and not (line.startswith('- ') or line.startswith('* ')):
            html_lines.append('</ul>')
            in_ul = False
        if in_ol and not re.match(r'^\d+\. ', line):
            html_lines.append('</ol>')
            in_ol = False
        
        # Blockquotes (grouped)
        if line.startswith('> '):
            if not in_blockquote:
                in_blockquote = True
                blockquote_lines = []
            blockquote_lines.append(process_inline(line[2:]))
            continue
        elif in_blockquote:
            html_lines.append(f'<blockquote>{" ".join(blockquote_lines)}</blockquote>')
            in_blockquote = False
            blockquote_lines = []
        
        # Headers
        if line.startswith('#### '):
            html_lines.append(f'<h4>{process_inline(line[5:])}</h4>')
            continue
        if line.startswith('### '):
            html_lines.append(f'<h3>{process_inline(line[4:])}</h3>')
            continue
        if line.startswith('## '):
            html_lines.append(f'<h2>{process_inline(line[3:])}</h2>')
            continue
        if line.startswith('# '):
            html_lines.append(f'<h1>{process_inline(line[2:])}</h1>')
            continue
        
        # Horizontal rule
        if line.strip() in ['---', '***', '___']:
            html_lines.append('<hr>')
            continue
        
        # Bullet lists
        if line.startswith('- ') or line.startswith('* '):
            if not in_ul:
                html_lines.append('<ul>')
                in_ul = True
            html_lines.append(f'<li>{process_inline(line[2:])}</li>')
            continue
        
        # Numbered lists
        ol_match = re.match(r'^(\d+)\. (.+)$', line)
        if ol_match:
            if not in_ol:
                html_lines.append('<ol>')
                in_ol = True
            html_lines.append(f'<li>{process_inline(ol_match.group(2))}</li>')
            continue
        
        # Empty lines
        if line.strip() == '':
            html_lines.append('')
            continue
        
        # Paragraphs
        html_lines.append(f'<p>{process_inline(line)}</p>')
    
    # Close open elements
    if in_ul:
        html_lines.append('</ul>')
    if in_ol:
        html_lines.append('</ol>')
    if in_blockquote:
        html_lines.append(f'<blockquote>{" ".join(blockquote_lines)}</blockquote>')
    
    return '\n'.join(html_lines)


def escape_html(text):
    """Escape HTML characters"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def process_inline(text):
    """Process inline formatting (bold, italic, links, code, images)"""
    # Images BEFORE links (otherwise ![alt](url) partially matches as link)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Code inline
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Highlight ==text==
    text = re.sub(r'==([^=]+)==', r'<mark>\1</mark>', text)
    # Bold (before italic to avoid conflicts)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    text = re.sub(r'(?<![a-zA-Z])_([^_]+)_(?![a-zA-Z])', r'<em>\1</em>', text)
    
    return text


def parse_frontmatter(content):
    """Extract simple YAML frontmatter and content"""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = {}
            for line in parts[1].strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip().strip('"\'')
            return frontmatter, parts[2].strip()
    return {}, content


def generate_html(title, content, is_index=False):
    """Generate a complete HTML page"""
    nav = '<nav><a href="/">Home</a></nav>' if not is_index else ''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{CSS}</style>
</head>
<body>
    <header>
        <a class="title" href="/">
            <h1><span class="logo">(╹ᴥ╹)</span> {BLOG_TITLE}</h1>
        </a>
        {nav}
    </header>
    <main>
        {content}
    </main>
    <footer>
        <p>Style inspired by <a href="https://bearblog.dev">Bear Blog</a></p>
    </footer>
</body>
</html>'''


def build():
    """Generate the static site"""
    posts_path = Path(POSTS_DIR)
    output_path = Path(OUTPUT_DIR)
    
    # Create directories
    posts_path.mkdir(exist_ok=True)
    output_path.mkdir(exist_ok=True)
    
    posts = []
    
    # Read all posts
    for md_file in posts_path.glob('*.md'):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        frontmatter, body = parse_frontmatter(content)
        
        title = frontmatter.get('title', md_file.stem.replace('-', ' ').title())
        date_str = frontmatter.get('date', datetime.now().strftime('%Y-%m-%d'))
        slug = md_file.stem
        
        posts.append({
            'title': title,
            'date': date_str,
            'slug': slug,
            'content': body
        })
        
        # Generate post page
        article_html = f'''
        <article>
            <header>
                <h1>{title}</h1>
                <time datetime="{date_str}">{date_str}</time>
            </header>
            {parse_markdown(body)}
            <a class="back-link" href="/">← Back</a>
        </article>
        '''
        
        page = generate_html(title, article_html)
        
        with open(output_path / f'{slug}.html', 'w', encoding='utf-8') as f:
            f.write(page)
        
        print(f'  {slug}.html')
    
    # Sort by date (newest first)
    posts.sort(key=lambda x: x['date'], reverse=True)
    
    # Generate index page
    posts_list = '<ul class="blog-posts">'
    for post in posts:
        posts_list += f'''
        <li>
            <span>{post['date']}</span>
            <a href="/{post['slug']}.html">{post['title']}</a>
        </li>'''
    posts_list += '</ul>'
    
    index_content = f'''
    <h2>{BLOG_SUBTITLE}</h2>
    <p>Welcome to my blog.</p>
    <h3>Posts</h3>
    {posts_list if posts else '<p><em>No posts yet. Add .md files to the posts/ folder.</em></p>'}
    '''
    
    index_page = generate_html(BLOG_TITLE, index_content, is_index=True)
    
    with open(output_path / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_page)
    
    print(f'  index.html')
    print(f'\nSite built in {OUTPUT_DIR}/')


def serve(port=8000):
    """Start a development server"""
    os.chdir(OUTPUT_DIR)
    
    handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Server running at http://localhost:{port}")
        print("Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


def create_example_post():
    """Create an example post"""
    posts_path = Path(POSTS_DIR)
    posts_path.mkdir(exist_ok=True)
    
    example = '''---
title: My first post
date: 2025-01-15
---

Welcome to my blog!

This is an example post written in **Markdown**. You can edit or delete it.

## Features

- Write in Markdown
- Automatic light/dark theme
- Fast and lightweight
- No JavaScript, no trackers

## Code example

```python
print("Hello, World!")
```

> "Simplicity is the ultimate sophistication." - Leonardo da Vinci

Happy writing!
'''
    
    example_file = posts_path / 'my-first-post.md'
    if not example_file.exists():
        with open(example_file, 'w', encoding='utf-8') as f:
            f.write(example)
        print(f'  Example post created: {example_file}')


def main():
    parser = argparse.ArgumentParser(
        description='Tiny Blog - Minimal static blog generator'
    )
    parser.add_argument('command', nargs='?', default='build',
                        choices=['build', 'serve', 'init'],
                        help='Command to run')
    parser.add_argument('-p', '--port', type=int, default=8000,
                        help='Port for the server (default: 8000)')
    
    args = parser.parse_args()
    
    print('Tiny Blog\n')
    
    if args.command == 'init':
        print('Initializing...')
        create_example_post()
        build()
    elif args.command == 'build':
        print('Building...')
        build()
    elif args.command == 'serve':
        if not Path(OUTPUT_DIR).exists():
            print('Building first...')
            build()
            print()
        serve(args.port)


if __name__ == '__main__':
    main()
