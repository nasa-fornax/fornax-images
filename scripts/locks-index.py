# Generate an html index for the lock files for gh-pages
# Assumes ./locks/ exit
import sys
from pathlib import Path


def generate_index(version=''):
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
        elif name.endswith("-lock.yml") or name == 'Project.toml.txt':
            display_name = name.replace("-lock.yml", "")
            display_name = display_name.replace('py-', '')
            if name == 'Project.toml.txt':
                display_name = 'Julia'
            conda_links.append(f"- [{display_name}]({rel_path})")

        # Group 3: TXT files
        elif name.endswith(".txt") and 'requirements' in name:
            # Strip both 'requirements-py-' and 'requirements-', plus '.txt'
            display_name = name.replace("requirements-py-", "") \
                               .replace("requirements-", "") \
                               .replace(".txt", "")
            txt_links.append(f"- [{display_name}]({rel_path})")

        # Catch-all for anything
        else:
            other_links.append(f"- [{rel_path}]({rel_path})")

    # Define the path for the output HTML file
    index_file = target_dir / "index.html"
    version_txt = f' for Version {version}'

    # Write out the HTML file
    with open(index_file, "w") as f:
        f.write(f"<!DOCTYPE html>\n<html>\n<head>\n<title>Fornax Installed Environments{version_txt}</title>\n")  # noqa
        f.write("<style>body { font-family: sans-serif; margin: 40px; line-height: 1.6; }</style>\n")  # noqa
        f.write("</head>\n<body>\n")

        f.write(f"<h1>Fornax Installed Environments{version_txt}</h1>\n")
        f.write(f"<p>The following files list the software packages installed for each environment in Fornax </p>\n")  # noqa

        f.write("<h2>Conda Environments</h2>\n<ul>\n")
        if conda_links:
            for link in conda_links:
                name, url = link.split("](")
                name = name.replace("- [", "")
                url = url.replace(")", "")
                f.write(f'<li><a href="{url}">{name}</a></li>\n')
        else:
            f.write("<li><em>No conda environments found.</em></li>\n")
        f.write("</ul>\n")

        f.write("<h2>pip Environments</h2>\n<ul>\n")
        if txt_links:
            for link in txt_links:
                name, url = link.split("](")
                name = name.replace("- [", "")
                url = url.replace(")", "")
                f.write(f'<li><a href="{url}">{name}</a></li>\n')
        else:
            f.write("<li><em>No requirements files found.</em></li>\n")
        f.write("</ul>\n")

        f.write("<h2>Internal Build Versions</h2>\n<ul>\n")
        if build_links:
            for link in build_links:
                name, url = link.split("](")
                name = name.replace("- [", "")
                url = url.replace(")", "")
                f.write(f'<li><a href="{url}">{name}</a></li>\n')
        else:
            f.write("<li><em>No build files found.</em></li>\n")
        f.write("</ul>\n")

        if other_links:
            f.write("<h2>Other Dependencies</h2>\n<ul>\n")
            for link in other_links:
                name, url = link.split("](")
                name = name.replace("- [", "")
                url = url.replace(")", "")
                f.write(f'<li><a href="{url}">{name}</a></li>\n')
            f.write("</ul>\n")

        f.write("</body>\n</html>")

    print(f"Successfully generated {index_file}")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        version = sys.argv[1]
    else:
        version = ''
    generate_index(version)
