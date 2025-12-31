import json
import os
import sys
from pathlib import Path


def strip_cell_ids(notebook):
    changed = False
    for cell in notebook.get("cells", []):
        if "id" in cell:
            cell.pop("id", None)
            changed = True
        metadata = cell.get("metadata")
        if isinstance(metadata, dict) and "id" in metadata:
            metadata.pop("id", None)
            changed = True
    return changed


def process_notebook(notebook_path):
    with notebook_path.open("r", encoding="utf-8") as f:
        notebook = json.load(f)

    changed = strip_cell_ids(notebook)

    if changed:
        with notebook_path.open("w", encoding="utf-8") as f:
            json.dump(notebook, f, ensure_ascii=False, indent=1)
            f.write("\n")
    return changed


def iter_notebooks(root_dir):
    skip_dirs = {".git", ".ipynb_checkpoints"}
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for filename in filenames:
            if filename.endswith(".ipynb"):
                yield Path(dirpath) / filename


def main():
    root_dir = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", ".lectures_output"))
    )

    if not root_dir.exists():
        print(f"Output directory {root_dir} does not exist; nothing to do.")
        return

    total = 0
    changed = 0
    for notebook_path in iter_notebooks(root_dir):
        total += 1
        if process_notebook(notebook_path):
            changed += 1
            print(f"Removed cell ids: {notebook_path}")

    print(f"Processed {total} notebook(s); updated {changed}.")


if __name__ == "__main__":
    main()
