#!/opt/envs/python3/bin/python

"""Archive a file or directory into a tar or tar.gz file
on the target filesystem."""

import os
import shutil
import tarfile
from pathlib import Path
import subprocess

import click

DEFAULT_OUTPUT_ROOT = Path("~/s3-storage").expanduser()


def _archive_name(source: Path, gzip: bool) -> str:
    """Return the archive filename for a source path."""
    if gzip:
        return f"{source.name}.tar.gz"
    return f"{source.name}.tar"


def _resolve_destination(source: Path, output: str | None, gzip: bool) -> Path:
    """Resolve the final archive path from the source and output option."""
    if output is None:
        return DEFAULT_OUTPUT_ROOT / _archive_name(source, gzip)

    # expand users' home path from ~/
    dest = Path(output).expanduser()
    # Check if the output is a directory
    if not (is_dir := str(dest).endswith(os.sep)):
        try:
            is_dir = dest.is_dir()
        except (OSError, ValueError):
            # S3 mount points may not support is_dir(), treat as file path
            pass

    if is_dir:
        return dest / _archive_name(source, gzip)
    return dest


def _ensure_parent(path: Path) -> None:
    """Create the destination parent directory if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)


def _add_source(tf: tarfile.TarFile, source: Path) -> None:
    """Add a path to the tar file if it is not a symlink"""
    def exclude_symlinks(tarinfo):
        if tarinfo.issym():
            return None  # Returning None skips this file/dir
        return tarinfo

    if source.is_file() or source.is_dir():
        tf.add(source, arcname=source.name, recursive=True,
               filter=exclude_symlinks)
    else:
        raise click.ClickException(f"Unsupported source type: {source}")


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "max_content_width": 100,
    },
    no_args_is_help=True,
)
@click.argument("source", type=click.Path(path_type=Path, exists=True,
                dir_okay=True, file_okay=True))
@click.option(
    "-o",
    "--output",
    type=str,
    default=None,
    help=("Output file path or directory. Defaults to "
          "~/s3-storage/<source>.tar"),
)
@click.option(
    "-c",
    "--compression",
    is_flag=True,
    help="Write a gzip-compressed tar.gz archive instead of a plain tar.",
)
@click.option(
    "--compression-level",
    type=click.IntRange(1, 9),
    default=6,
    show_default=True,
    help="Gzip compression level when --compression is set.",
)
@click.option("--force", is_flag=True, help="Overwrite an existing archive.")
@click.option(
    "--remove-source",
    is_flag=True,
    help=("Remove the source file or directory after the archive "
          "is written successfully."),
)
def main(
    source: Path,
    output: str | None,
    compression: bool,
    compression_level: int,
    force: bool,
    remove_source: bool,
) -> None:
    """Archive a file or directory into a tar or tar.gz file."""
    source = source.expanduser().resolve()
    gzip = compression
    dest_path = _resolve_destination(source, output, gzip)
    _ensure_parent(dest_path)

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if not force:
        flags |= os.O_EXCL

    try:
        fd = os.open(dest_path, flags, 0o644)
    except FileExistsError:
        raise click.ClickException(f"Destination already exists: {dest_path}")
    except IsADirectoryError:
        raise click.ClickException(f"Destination is a directory: {dest_path}")

    try:
        with os.fdopen(fd, "wb") as f:
            # 1. Build the tar command
            tar_cmd = ["tar", "-c"]

            # Both pigz and gzip read the GZIP env variable for the
            # compression level!
            env = os.environ.copy()
            if gzip:
                env["GZIP"] = f"-{compression_level}"

                # Use pigz if available, otherwise fallback to standard gzip
                if shutil.which("pigz"):
                    tar_cmd.extend(["-I", "pigz"])
                else:
                    tar_cmd.append("-z")

            # -f "-" tells tar to write to stdout.
            # -C changes directory to the parent so the tarball
            # paths are relative.
            tar_cmd.extend(["-f", "-", "-C", str(source.parent), source.name])

            # 2. Run the subprocess, piping stdout directly to your
            # file object (f)
            try:
                subprocess.run(
                    tar_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    check=True,
                    text=True  # Decodes stderr to string
                )
            except subprocess.CalledProcessError as e:
                raise click.ClickException(f"Tar command failed: {e.stderr}")

            # 3. Ensure all data flushed to the mountpoint
            f.flush()
            try:
                os.fsync(f.fileno())
            except (OSError, AttributeError):
                pass

        # 4. Handle source removal after successful close
        if remove_source:
            if source.is_dir():
                shutil.rmtree(source)
            else:
                source.unlink()

    except Exception:
        # fp is closed by with; just delete the broken file on failure.
        if dest_path.exists():
            try:
                dest_path.unlink()
            except OSError:
                pass
        raise


if __name__ == "__main__":
    main()
