import argparse
import logging

from buildimages import Base
from buildimages import order


class Tagger(Base):
    def tag(self, repository, release_name, source_tag):
        for name in order:
            source = f"ghcr.io/{repository}/{name}:{source_tag}"
            self.run(f"docker pull {source}", 1000)
            target = f"ghcr.io/{repository}/{name}:{release_name}"
            tagcommand = f"docker tag {source} {target}"
            result = self.run(tagcommand, 500)
            self.out(result)
            result = self.run(f"docker push {target}", 1000)
            self.out(result)


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
    logging.basicConfig(
        format="%(asctime)s|%(levelname)5s| %(message)s",
        datefmt="%Y-%m-%d|%H:%M:%S",
    )
    args = ap.parse_args()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    tagger = Tagger(logger)
    tagger.tag(args.repository, args.release_name, args.source_tag)
