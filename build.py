#!/usr/bin/env python3
"""
Recipe site generator.

Reads recipes.json, shaped like:

  {
    "Category Name": {
      "Recipe Title": {
        "title": "...",
        "image": "./imgs/recipes/whatever.jpg",   # optional, "" if none
        "source": "...",                           # optional
        "subcategory": "Poultry",                  # optional, secondary filter/label
        "prep": "20 minutes",                      # optional
        "cook": "10 minutes",                      # optional
        "yield": "4 servings",                     # optional
        "ingredients": ["...", "..."],
        "steps": ["...", "..."]
      }
    }
  }

...and generates:
  - site/index.html            a browsable, filterable recipe box
  - site/recipes/<slug>.html   one page per recipe
  - site/imgs/...              images that actually exist get copied over

Usage:
  python3 build.py

No external dependencies -- just the Python standard library.
"""
import json
import re
import shutil
import html
import sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent
RECIPES_FILE = ROOT / "recipes.json"
OUTPUT_DIR = ROOT / "site"
ASSETS_DIR = ROOT / "assets"

# Tab colors are assigned to categories in the order they're first seen in
# recipes.json, cycling through this palette.
TAB_PALETTE = ["#B5533C", "#5C7A8A", "#7A8450", "#9B6A9E", "#C08A3E", "#4E6E5D"]


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def esc(text) -> str:
    return html.escape(str(text), quote=True)


def load_recipes():
    """Flatten the nested {category: {title: recipe}} structure into a
    list of recipe dicts, each carrying its category and a unique slug."""
    if not RECIPES_FILE.exists():
        sys.exit(f"Can't find {RECIPES_FILE.name} next to build.py.")

    try:
        raw = json.loads(RECIPES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(
            f"recipes.json isn't valid JSON: {e}\n"
            f"  -> check around line {e.lineno}, column {e.colno} "
            f"(a trailing comma is a common culprit)."
        )

    recipes = []
    used_slugs = set()
    for category, titles in raw.items():
        for title_key, data in titles.items():
            title = data.get("title", title_key)
            slug = slugify(title)
            if slug in used_slugs:
                slug = slugify(f"{category}-{title}")
            used_slugs.add(slug)

            recipe = dict(data)
            recipe["title"] = title
            recipe["category"] = category
            recipe["slug"] = slug
            recipes.append(recipe)

    recipes.sort(key=lambda r: r["title"])
    return recipes


def assign_tab_colors(recipes):
    colors = {}
    for r in recipes:
        cat = r["category"]
        if cat not in colors:
            colors[cat] = TAB_PALETTE[len(colors) % len(TAB_PALETTE)]
    return colors


def render_ingredients(ingredients):
    """Ingredients can be either a flat list of strings, or a dict mapping
    section names to lists of strings (e.g. "For the Batter": [...],
    "For the Streusel": [...]). Render either shape appropriately."""
    if isinstance(ingredients, dict):
        parts = []
        for section_name, items in ingredients.items():
            items_html = "\n".join(f'<li>{esc(i)}</li>' for i in items)
            parts.append(f"""
            <div class="ingredient-section">
              <h3>{esc(section_name)}</h3>
              <ul>{items_html}</ul>
            </div>""")
        return "".join(parts)
    else:
        items_html = "\n".join(f'<li>{esc(i)}</li>' for i in ingredients)
        return f"<ul>{items_html}</ul>"


def resolve_image(recipe, from_dir_depth):
    """Return a site-relative image path if the recipe has one AND the file
    actually exists on disk, else None. from_dir_depth 0 = site root
    (index.html), 1 = one level down (site/recipes/*.html)."""
    raw_path = (recipe.get("image") or "").strip()
    if not raw_path:
        return None

    clean = raw_path.lstrip("./")
    source_path = ROOT / clean
    if not source_path.exists():
        return None

    prefix = "../" * from_dir_depth
    return prefix + clean


PAGE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{css_path}">
</head>
<body>
"""

PAGE_FOOT = """
</body>
</html>
"""


def render_index(recipes, tab_colors):
    categories = sorted(set(r["category"] for r in recipes))

    # Map each category to the sorted set of subcategories used within it,
    # so the page can offer a secondary filter once a category is chosen.
    category_subcats = {}
    for r in recipes:
        sub = (r.get("subcategory") or "").strip()
        if sub:
            category_subcats.setdefault(r["category"], set()).add(sub)
    category_subcats = {c: sorted(s) for c, s in category_subcats.items()}

    cat_buttons = ['<button class="filter-btn active" data-filter="all">All</button>']
    for c in categories:
        cat_buttons.append(
            f'<button class="filter-btn" data-filter="{esc(c)}" '
            f'style="--tab-color:{tab_colors[c]}">{esc(c)}</button>'
        )

    cards = []
    for r in recipes:
        color = tab_colors[r["category"]]
        image = resolve_image(r, from_dir_depth=0)
        thumb_html = (
            f'<div class="card-thumb"><img src="{esc(image)}" alt="" loading="lazy"></div>'
            if image else ""
        )
        meta_bits = []
        if r.get("prep"):
            meta_bits.append(f'<span>{esc(r["prep"])} prep</span>')
        if r.get("cook"):
            meta_bits.append(f'<span>{esc(r["cook"])} cook</span>')
        if r.get("yield"):
            meta_bits.append(f'<span>{esc(r["yield"])}</span>')

        source_html = ""
        src = (r.get("source") or "").strip()
        if src:
            source_html = f'<p class="card-source">from {esc(src)}</p>'

        subcat = (r.get("subcategory") or "").strip()
        subcat_html = f'<span class="subcat-badge">{esc(subcat)}</span>' if subcat else ""

        cards.append(f"""
        <a class="card" href="recipes/{esc(r['slug'])}.html"
           data-category="{esc(r['category'])}" data-subcategory="{esc(subcat)}"
           data-search="{esc(r['title'].lower())}">
          <span class="card-tab" style="background:{color}"></span>
          {thumb_html}
          <div class="card-body">
            <h2>{esc(r['title'])}</h2>
            {subcat_html}
            {source_html}
            <div class="card-meta">{''.join(meta_bits)}</div>
          </div>
        </a>""")

    body = f"""
<header class="site-header">
  <h1>The Recipe Box</h1>
  <p class="tagline">{len(recipes)} recipes, kept close at hand.</p>
</header>

<div class="toolbar">
  <input id="search" type="search" placeholder="Search recipes..." autocomplete="off">
  <div class="filters">{''.join(cat_buttons)}</div>
  <div class="filters subfilters" id="subcategory-filters" hidden></div>
</div>

<main class="card-grid" id="card-grid">
  {''.join(cards)}
</main>

<p id="no-results" class="no-results" hidden>No recipes match that search.</p>

<footer class="site-footer">
  <p>Built on {date.today().isoformat()}. {len(recipes)} recipes in the box.</p>
</footer>

<script id="category-subcats" type="application/json">{json.dumps(category_subcats)}</script>
<script src="assets/site.js"></script>
"""
    html_out = PAGE_HEAD.format(title="The Recipe Box", css_path="assets/style.css") + body + PAGE_FOOT
    (OUTPUT_DIR / "index.html").write_text(html_out, encoding="utf-8")


def render_recipe_page(recipe, tab_colors):
    color = tab_colors[recipe["category"]]
    image = resolve_image(recipe, from_dir_depth=1)
    hero_html = (
        f'<div class="hero-image"><img src="{esc(image)}" alt="{esc(recipe["title"])}"></div>'
        if image else ""
    )

    ingredients_html = render_ingredients(recipe.get("ingredients", []))
    steps_html = "\n".join(f'<li>{esc(s)}</li>' for s in recipe.get("steps", []))

    meta_bits = []
    if recipe.get("prep"):
        meta_bits.append(f'<div class="meta-item"><span class="meta-label">Prep</span>{esc(recipe["prep"])}</div>')
    if recipe.get("cook"):
        meta_bits.append(f'<div class="meta-item"><span class="meta-label">Cook</span>{esc(recipe["cook"])}</div>')
    if recipe.get("yield"):
        meta_bits.append(f'<div class="meta-item"><span class="meta-label">Yield</span>{esc(recipe["yield"])}</div>')

    source_html = ""
    src = (recipe.get("source") or "").strip()
    if src:
        if src.startswith("http://") or src.startswith("https://"):
            source_html = f'<p class="source">Source: <a href="{esc(src)}">{esc(src)}</a></p>'
        else:
            source_html = f'<p class="source">Source: {esc(src)}</p>'

    subcat = (recipe.get("subcategory") or "").strip()
    subcat_html = f'<span class="card-tab-large subcat-pill">{esc(subcat)}</span>' if subcat else ""

    body = f"""
<div class="recipe-page">
  <a class="back-link" href="../index.html">&larr; Back to the box</a>
  <article class="index-card" style="--tab-color:{color}">
    <div class="punch-holes"><span></span><span></span><span></span></div>
    <span class="card-tab-large" style="background:{color}">{esc(recipe['category'])}</span>{subcat_html}
    <h1>{esc(recipe['title'])}</h1>
    {hero_html}
    {source_html}
    <div class="meta-row">{''.join(meta_bits)}</div>

    <div class="recipe-columns">
      <section class="ingredients">
        <h2>Ingredients</h2>
        {ingredients_html}
      </section>
      <section class="steps">
        <h2>Steps</h2>
        <ol>{steps_html}</ol>
      </section>
    </div>
  </article>
</div>
"""
    html_out = PAGE_HEAD.format(
        title=f"{recipe['title']} \u2014 The Recipe Box", css_path="../assets/style.css"
    ) + body + PAGE_FOOT
    out_path = OUTPUT_DIR / "recipes" / f"{recipe['slug']}.html"
    out_path.write_text(html_out, encoding="utf-8")


def copy_images(recipes):
    """Copy only the image files that are actually referenced and exist,
    preserving their relative path under site/."""
    for r in recipes:
        raw_path = (r.get("image") or "").strip()
        if not raw_path:
            continue
        clean = raw_path.lstrip("./")
        source_path = ROOT / clean
        if not source_path.exists():
            continue
        dest_path = OUTPUT_DIR / clean
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)


def main():
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    (OUTPUT_DIR / "recipes").mkdir(parents=True)
    shutil.copytree(ASSETS_DIR, OUTPUT_DIR / "assets")

    recipes = load_recipes()
    if not recipes:
        print("No recipes found in recipes.json.")
        return

    missing_images = [r["title"] for r in recipes if (r.get("image") or "").strip()
                       and not (ROOT / r["image"].lstrip("./")).exists()]

    tab_colors = assign_tab_colors(recipes)
    render_index(recipes, tab_colors)
    for r in recipes:
        render_recipe_page(r, tab_colors)
    copy_images(recipes)

    print(f"Built {len(recipes)} recipe(s) into {OUTPUT_DIR}/")
    for r in recipes:
        print(f"  - [{r['category']}] {r['title']}  ->  site/recipes/{r['slug']}.html")
    if missing_images:
        print(f"\nNote: {len(missing_images)} recipe(s) list an image path that "
              f"doesn't exist on disk, so they'll render without one:")
        for title in missing_images:
            print(f"  - {title}")


if __name__ == "__main__":
    main()
