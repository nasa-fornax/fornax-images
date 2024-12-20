import argparse
import logging

from buildimages import Base
from buildimages import order


class Tagger(Base):
    def tag(self, repository, release_name, source_tag, symbolic_tag):
        for name in order:
            source = f"ghcr.io/{repository}/{name}:{source_tag}"
            self.run(f"docker pull {source}", 1000)

            releasetarget = f"ghcr.io/{repository}/{name}:{release_name}"
            releasetagcommand = f"docker tag {source} {releasetarget}"
            self.out(self.run(releasetagcommand, 500))
            self.out(self.run(f"docker push {releasetarget}", 1000))

            symbolictarget = f"ghcr.io/{repository}/{name}:{symbolic_tag}"
            symbolictagcommand = f"docker tag {source} {symbolictarget}"
            self.out(self.run(symbolictagcommand, 500))
            self.out(self.run(f"docker push {symbolictarget}", 1000))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "repository", help="GH repository name (e.g. 'fornax-core/images')"
    )
    ap.add_argument("release_name", help="Release name (e.g. 'v0.0.1')")
    ap.add_argument(
        "--source_tag",
        help="CR source tag name (e.g. 'main')",
        default="main",
    )
    ap.add_argument(
        "--symbolic_tag",
        help="CR symbolic target tag name (e.g. 'stable')",
        default="stable",
    )
    logging.basicConfig(
        format="%(asctime)s|%(levelname)5s| %(message)s",
        datefmt="%Y-%m-%d|%H:%M:%S",
    )
    args = ap.parse_args()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    tagger = Tagger(logger)
    tagger.tag(
        args.repository, args.release_name, args.source_tag, args.symbolic_tag
    )
