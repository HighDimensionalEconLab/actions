"""Convert RevealJS HTML slides to PDF using Playwright.

Walks QUARTO_PROJECT_OUTPUT_DIR for RevealJS HTML files, uses source .qmd
hash-based caching, and generates PDFs via Playwright's bundled Chromium.

Environment variables:
    QUARTO_PROJECT_OUTPUT_DIR  Output directory (default: .lectures_output)
    PDF_CACHE_DIR              Cache directory (default: .pdf_cache)
    CI                         If set, adds --no-sandbox etc. to browser args
"""

import asyncio
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

from playwright.async_api import async_playwright

SLIDE_WIDTH = 1280
SLIDE_HEIGHT = 720

# RevealJS print-pdf mode sets display:inline-block on slide children for
# vertical centering.  Chromium's print engine treats inline-block as an
# atomic box that cannot be split across page boundaries.  When the 10%
# RevealJS margin makes the slide section taller than the PDF page, later
# slides progressively drift off the page boundary.  An inline-block child
# that doesn't fit in the remaining page space is pushed out entirely,
# producing a blank page.  Forcing display:block on list elements in print
# media fixes this without affecting flex column layouts or tables.
PRINT_FIX_CSS = """
@media print {
    .reveal .slides section > ul,
    .reveal .slides section > ol {
        display: block !important;
    }
}
"""


def compute_file_hash(file_path: str) -> str:
    hash_algo = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_algo.update(chunk)
    return hash_algo.hexdigest()


def is_revealjs_file(filepath: str) -> bool:
    with open(filepath, "r", errors="ignore") as f:
        content = f.read()
        return "site_libs/revealjs" in content


async def convert_slide(page, html_file_path: str, cache_pdf_path: str) -> bool:
    """Convert a single RevealJS HTML file to PDF. Returns True on success."""
    file_url = f"file://{os.path.abspath(html_file_path)}?print-pdf"
    print(f"  Converting: {html_file_path} -> {cache_pdf_path}")

    try:
        await page.goto(file_url, wait_until="networkidle", timeout=60000)

        # Wait for MathJax to finish rendering (if present)
        try:
            await page.evaluate("() => MathJax.startup.promise")
            print(f"    MathJax rendering complete")
        except Exception:
            print(f"    No MathJax detected (or already done)")

        # Fix inline-block elements that cause blank pages in print mode
        await page.add_style_tag(content=PRINT_FIX_CSS)

        # Brief pause for RevealJS print-pdf CSS restructuring
        await page.wait_for_timeout(2000)

        await page.pdf(
            path=cache_pdf_path,
            width=f"{SLIDE_WIDTH}px",
            height=f"{SLIDE_HEIGHT}px",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        print(f"    Done: {cache_pdf_path}")
        return True

    except Exception as e:
        print(f"    ERROR converting {html_file_path}: {e}", file=sys.stderr)
        return False


async def generate_pdfs(output_dir: str, cache_dir: str) -> int:
    """Walk output_dir for RevealJS HTML files, convert to PDF with caching.

    Returns the number of failures (0 = success).
    """
    os.makedirs(cache_dir, exist_ok=True)
    hash_file = os.path.join(cache_dir, ".html_hashes.json")

    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            previous_hashes = json.load(f)
    else:
        previous_hashes = {}

    # Collect RevealJS HTML files
    slides = []
    for dirpath, _dirnames, filenames in os.walk(output_dir):
        if "site_libs" in dirpath:
            continue
        for filename in filenames:
            if filename.endswith(".html"):
                html_file_path = os.path.join(dirpath, filename)
                if is_revealjs_file(html_file_path):
                    slides.append(html_file_path)

    if not slides:
        print("No RevealJS HTML files found.")
        return 0

    print(f"Found {len(slides)} RevealJS slide(s)")

    # Determine browser args for CI
    browser_args = []
    if os.environ.get("CI"):
        browser_args = ["--no-sandbox", "--disable-gpu", "--disable-setuid-sandbox"]

    current_hashes = {}
    failures = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=browser_args)
        page = await browser.new_page()

        for html_file_path in slides:
            relative_path = os.path.relpath(html_file_path, output_dir)

            # Hash the source .qmd file for caching
            source_path = os.path.splitext(relative_path)[0] + ".qmd"
            source_hash = compute_file_hash(source_path)
            current_hashes[relative_path] = source_hash

            # Cache filename based on path hash
            path_hash = hashlib.md5(relative_path.encode("utf-8")).hexdigest()
            cache_pdf_name = f"{path_hash}.pdf"
            cache_pdf_path = os.path.join(cache_dir, cache_pdf_name)

            # Output PDF path (alongside HTML)
            pdf_file_name = os.path.splitext(os.path.basename(html_file_path))[0] + ".pdf"
            pdf_file_path = os.path.join(os.path.dirname(html_file_path), pdf_file_name)

            if (
                previous_hashes.get(relative_path) == source_hash
                and os.path.exists(cache_pdf_path)
            ):
                print(f"Using cached PDF for {html_file_path}")
            else:
                success = await convert_slide(page, html_file_path, cache_pdf_path)
                if not success:
                    failures += 1
                    continue

            # Copy the PDF from cache to the output directory
            shutil.copy2(cache_pdf_path, pdf_file_path)

        await browser.close()

    # Write updated hashes
    with open(hash_file, "w") as f:
        json.dump(current_hashes, f)

    print(f"\nFinished: {len(slides) - failures}/{len(slides)} succeeded")
    return failures


if __name__ == "__main__":
    output_dir = os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", ".lectures_output")
    cache_dir = os.environ.get("PDF_CACHE_DIR", ".pdf_cache")
    print(
        f"Generating PDFs for RevealJS slides in {output_dir}. Cache: {cache_dir}"
    )
    failures = asyncio.run(generate_pdfs(output_dir, cache_dir))
    sys.exit(1 if failures else 0)
