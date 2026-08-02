#!/usr/bin/env python3

"""Archive a file or directory into a tar or tar.gz file on the target filesystem."""

import os
import shutil
import tarfile
from pathlib import Path

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


def _add_path(tf: tarfile.TarFile, path: Path, arcname: str) -> None:
    """Add a path to the tar stream."""
    if path.is_dir() and not path.is_symlink():
        # don't follow symlinks....
        tf.add(path, arcname=arcname, recursive=False)
        with os.scandir(path) as entries:
            for entry in entries:
                entry_arcname = f"{arcname}/{entry.name}"
                if entry.is_dir(follow_symlinks=False):
                    _add_path(tf, Path(entry.path), entry_arcname)
                else:
                    tf.add(entry.path, arcname=entry_arcname, recursive=False)
        return

    tf.add(path, arcname=arcname, recursive=False)


def _add_source(tf: tarfile.TarFile, source: Path) -> None:
    """Add the requested source file or directory to the tarball."""
    if source.is_file():
        tf.add(source, arcname=source.name, recursive=False)
        return

    if source.is_dir():
        _add_path(tf, source, source.name)
        return

    raise click.ClickException(f"Unsupported source type: {source}")


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "max_content_width": 100,
    },
    no_args_is_help=True,
)
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=True, file_okay=True))
@click.option(
    "-o",
    "--output",
    type=str,
    default=None,
    help="Output file path or directory. Defaults to ~/s3-data/<source>.tar",
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
    help="Remove the source file or directory after the archive is written successfully.",
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
    # expand users' home path from ~/
    source = source.expanduser().resolve()
    gzip = compression
    dest_path = _resolve_destination(source, output, gzip)
    _ensure_parent(dest_path)

    # Create the destination file and overwrite any existing file.
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if not force:
        # Fail if the destination already exists unless overwrite was requested.
        # O_EXCL ensures atomic check-and-create for most filesystems.
        # For filesystems that don't support O_EXCL (e.g., some network mounts),
        # this may raise OSError which we handle below.
        flags |= os.O_EXCL

    try:
        fd = os.open(dest_path, flags, 0o644)
    except FileExistsError:
        raise click.ClickException(f"Destination already exists: {dest_path}")
    except IsADirectoryError:
        raise click.ClickException(f"Destination is a directory: {dest_path}")

    try:
        with os.fdopen(fd, "wb") as f:
            mode = "w|gz" if gzip else "w|"
            compress_level = compression_level if gzip else None

            with tarfile.open(fileobj=f, mode=mode, compresslevel=compress_level) as tf:
                _add_source(tf, source)
            # ensure all data flushed to the mountpoint before closing the file.
            f.flush()
            try:
                os.fsync(f.fileno())
            except (OSError, AttributeError):
                # fsync may not be supported on some mount points (e.g., S3),
                # but we can skip safely
                pass
        if remove_source:
            if source.is_dir():
                shutil.rmtree(source)
            else:
                source.unlink()
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


if __name__ == "__main__":
    main()
