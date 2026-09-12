# The Recipe Box

A small static site generator that turns your `recipes.json` file into a
browsable, searchable HTML recipe site — hosted for free on GitHub Pages.

```
recipe-site/
  recipes.json        <- your recipe database (one big file, as you have it)
  build.py             <- turns recipes.json into site/*.html
  assets/              <- CSS + JS for the generated site
  imgs/recipes/        <- put recipe images here (optional)
  site/                <- generated output (created by build.py, not committed)
  .github/workflows/   <- auto-builds and publishes on every push
```

## Your data format

This is built directly around the structure you're already using — nested
by category, then by recipe title:

```jsonc
{
  "Breakfast": {
    "Baked Baguette French Toast": {
      "title": "Baked Baguette French Toast",
      "image": "./imgs/recipes/some-file.jpg",   // optional, "" is fine
      "source": "",                               // optional
      "prep": "20 minutes",                       // optional, free text
      "cook": "10 minutes",                       // optional, free text
      "yield": "4 servings",                      // optional, free text
      "ingredients": ["...", "..."],
      "steps": ["...", "..."]
    }
  },
  "Dinner": {
    "...": { }
  }
}
```

**Replace `recipes.json` with your real file** (same shape) before your
first build. Everything else in this kit works unchanged.

### About images

Most of your recipes probably don't have a real image file yet. That's
handled: at build time, the script checks whether the file at `image`
actually exists on disk. If it doesn't, that recipe just renders without a
picture — no broken image icons. When you do have an image, drop it
wherever the `image` path says (by default, alongside this project in
`imgs/recipes/`) and it'll show up automatically next build.

### A note on your JSON

Make sure `recipes.json` is valid JSON — in particular, no trailing commas
after the last item in a list (e.g. `["a", "b",]` is invalid; `["a", "b"]`
is fine). If `build.py` hits a parse error, it will tell you the exact line
and column to check.

## One-time setup

1. **Create a GitHub account** if you don't have one: https://github.com/signup
   (free).

2. **Create a new repository** on github.com (e.g. name it `recipes`). Public
   repos get free GitHub Pages; private repos need GitHub Pro/Team for Pages.

3. **Push this folder** to that repository:

   ```bash
   git init
   git add .
   git commit -m "Initial recipe site"
   git branch -M main
   git remote add origin https://github.com/<your-username>/recipes.git
   git push -u origin main
   ```

4. **Turn on GitHub Pages with Actions as the source.** In your repo:
   Settings → Pages → under "Build and deployment," set **Source** to
   **GitHub Actions**.

5. Check the **Actions** tab for a green checkmark after a minute or so.
   Your site will be live at:

   ```
   https://<your-username>.github.io/recipes/
   ```

   (Exact URL is under Settings → Pages once the first deploy finishes.)

## Adding a new recipe

From your home computer, the everyday workflow:

1. Open `recipes.json`.
2. Add a new entry under an existing category, or add a whole new category
   key, following the shape above.
3. Commit and push:

   ```bash
   git add recipes.json
   git commit -m "Add lemon cake"
   git push
   ```

GitHub Actions rebuilds and republishes the site automatically within about
a minute of the push — you don't need to run Python yourself for this.

## Previewing locally before you push

```bash
python3 build.py
```

This writes the finished site into `site/`. To view it properly (some
browsers block local scripts when you just double-click the HTML file):

```bash
cd site && python3 -m http.server 8000
```

Then visit http://localhost:8000

## Editing the look

- Colors, fonts, and layout: `assets/style.css`
- Category tab colors are assigned automatically in the order categories
  first appear in `recipes.json` (see `TAB_PALETTE` at the top of `build.py`)
- Search/filter behavior: `assets/site.js`

## If your JSON file grows unwieldy

One big file is completely fine at the scale of a personal recipe
collection, and it's what this kit is built for now. If it ever gets large
enough that hand-editing feels risky, or you want per-recipe files for
cleaner version history, that's a straightforward follow-up — just ask, and
the build script can be adapted to read a folder of files instead without
you needing to touch your existing data by hand.
