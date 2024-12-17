import argparse
import logging
import json
import subprocess

from buildimages import order
from buildimages import Base


class Needer(Base):
    def needs(self, repository, gh_token, dirs_changed, branch):
        if isinstance(dirs_changed, str):
            dirs_changed = json.loads(dirs_changed)
        images_changed = set()
        for image_name in order:
            for fn in dirs_changed:
                if fn.startswith(image_name):
                    images_changed.add(image_name)
        needed = []
        for image_name in order:
            try:
                result = self.run(
                    f'curl -s -H "Authorization: Bearer {gh_token}" '
                    f"https://ghcr.io/v2/{repository}/{image_name}/tags/list",
                    500,
                    capture_output=True,
                )
                tags = json.loads(result.stdout)["tags"]
                if (image_name in images_changed) or (not branch in tags):
                    needed.append(image_name)
            except subprocess.CalledProcessError:
                needed.append(image_name)

        return needed


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "repository", help="GH repository name (e.g. 'fornax-core/images')"
    )
    ap.add_argument("gh_token", help="Github token(already base64ed)")
    ap.add_argument("dirs_changed", help="JSON of directories changed")
    ap.add_argument("branch", help="Branch in repo")
    logging.basicConfig(
        format="%(asctime)s|%(levelname)5s| %(message)s",
        datefmt="%Y-%m-%d|%H:%M:%S",
    )
    args = ap.parse_args()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    needer = Needer(logger)
    print(
        " ".join(
            needer.needs(
                args.repository, args.gh_token, args.dirs_changed, args.branch
            )
        )
    )
