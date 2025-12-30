import hashlib
import json
import os
import shutil
import subprocess


def compute_file_hash(file_path):
    hash_algo = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_algo.update(chunk)
    return hash_algo.hexdigest()


def is_revealjs_file(filepath):
    with open(filepath, "r", errors="ignore") as f:
        content = f.read()
        return "site_libs/revealjs" in content


def run_decktape_on_html(root_dir, cache_dir=".pdf_cache"):
    os.makedirs(cache_dir, exist_ok=True)
    hash_file = os.path.join(cache_dir, ".html_hashes.json")

    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            previous_hashes = json.load(f)
    else:
        previous_hashes = {}

    current_hashes = {}
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip 'site_libs' directory
        if "site_libs" in dirpath:
            continue
        for filename in filenames:
            if filename.endswith(".html"):
                html_file_path = os.path.join(dirpath, filename)
                if not is_revealjs_file(html_file_path):
                    continue

                relative_path = os.path.relpath(html_file_path, root_dir)
                # html_hash = compute_file_hash(html_file_path)
                source_path = os.path.splitext(relative_path)[0] + ".qmd"
                source_hash = compute_file_hash(source_path)
                current_hashes[relative_path] = source_hash

                # Generate unique cache filename using hash of relative path
                path_hash = hashlib.md5(relative_path.encode("utf-8")).hexdigest()
                cache_pdf_name = f"{path_hash}.pdf"
                cache_pdf_path = os.path.join(cache_dir, cache_pdf_name)

                pdf_file_name = filename.replace(".html", ".pdf")
                pdf_file_path = os.path.join(dirpath, pdf_file_name)

                if (
                    previous_hashes.get(relative_path) == source_hash
                ) and os.path.exists(cache_pdf_path):
                    print(f"Using cached PDF for {html_file_path}")
                else:
                    print(f"Converting {html_file_path} to {cache_pdf_path}")
                    cli_cmd = f"decktape --chrome-arg=--no-sandbox --chrome-arg=--disable-gpu --chrome-arg=--disable-setuid-sandbox {html_file_path} {cache_pdf_path}"
                    subprocess.run(cli_cmd, shell=True, check=True)

                # Copy the PDF from cache to the output directory
                shutil.copy2(cache_pdf_path, pdf_file_path)

    with open(hash_file, "w") as f:
        json.dump(current_hashes, f)


if __name__ == "__main__":
    output_dir = os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", ".lectures_output")
    cache_dir = os.environ.get("PDF_CACHE_DIR", ".pdf_cache")
    print(
        f"Running decktape on all revealjs html files in {output_dir}. PDFs cached in {cache_dir}"
    )
    run_decktape_on_html(output_dir, cache_dir)
