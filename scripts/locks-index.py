# Generate an html index for the lock files for gh-pages
# Assumes ./locks/ exit
import sys
from pathlib import Path


def generate_index():
    # Define the directory containing your files
    target_dir = Path("locks")

    # Ensure the directory exists before proceeding
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"Error: Directory '{target_dir}' not found.")
        sys.exit(1)

    conda_links = []
    txt_links = []
    build_links = []
    other_links = []

    # Scan the target directory
    for path in sorted(target_dir.rglob("*")):
        # Skip directories and the index files themselves
        if not path.is_file() or path.name in ["index.html", "index.md"]:
            continue

        # Get the relative path for the actual hyperlink
        rel_path = path.relative_to(target_dir).as_posix()
        name = path.name

        # Group 1: Build files
        if name.startswith("build-"):
            build_links.append(f"- [{name}]({rel_path})")

        # Group 2: Conda lock files
        elif name.endswith("-lock.yml"):
            display_name = name.replace("-lock.yml", "")
            conda_links.append(f"- [{display_name}]({rel_path})")

        # Group 3: TXT files
        elif name.endswith(".txt"):
            # Strip both 'requirements-py-' and 'requirements-', plus '.txt'
            display_name = name.replace("requirements-py-", "") \
                               .replace("requirements-", "") \
                               .replace(".txt", "")
            txt_links.append(f"- [{display_name}]({rel_path})")

        # Catch-all for anything else (like julia/Manifest.toml)
        else:
            other_links.append(f"- [{rel_path}]({rel_path})")

    # Define the path for the output Markdown file
    index_file = target_dir / "index.md"

    # Write out the Markdown file
    with open(index_file, "w") as f:
        f.write("# CI Generated Locks\n\n")

        f.write("## Conda Environments\n")
        if conda_links:
            f.write("\n".join(conda_links) + "\n\n")
        else:
            f.write("*No conda environments found.*\n\n")

        f.write("## pip Environments\n")
        if txt_links:
            f.write("\n".join(txt_links) + "\n\n")
        else:
            f.write("*No requirements files found.*\n\n")

        f.write("## Build Files\n")
        if build_links:
            f.write("\n".join(build_links) + "\n\n")
        else:
            f.write("*No build files found.*\n\n")

        if other_links:
            f.write("## Other Dependencies\n")
            f.write("\n".join(other_links) + "\n")

    print(f"Successfully generated {index_file}")


if __name__ == "__main__":
    generate_index()
