# Tiny Blog

A minimal static blog generator. No dependencies, just Python.

Inspired by [Bear Blog](https://bearblog.dev).

## Usage

### Initialize

```
python bear.py init
```

Creates an example post and builds the site.

### Write posts

Add `.md` files to the `posts/` folder:

```markdown
---
title: Post title
date: 2025-01-15
---

Your content in Markdown.
```

### Build

```
python bear.py build
```

Generates HTML files in `public/`.

### Preview

```
python bear.py serve
```

Opens a local server at http://localhost:8000

### Deploy

Upload the `public/` folder to any static host (GitHub Pages, Netlify, etc).

## Configuration

Edit the variables at the top of `bear.py`:

```python
BLOG_TITLE = "My Blog"
BLOG_SUBTITLE = "A minimal, no-nonsense blog"
```

## Markdown

Supported syntax:

- `# ## ### ####` headings
- `**bold**` and `*italic*`
- `[link](url)` and `![image](url)`
- `` `code` `` and fenced code blocks
- `- item` and `1. item` lists
- `> quote` blockquotes
- `==highlight==`
- `---` horizontal rule

## Structure

```
my-blog/
  bear.py
  posts/
    post-one.md
    post-two.md
  public/
    index.html
    post-one.html
    post-two.html
```

## License

Style derived from Bear Blog by Herman Martinus.
See LICENSE.md for terms.
