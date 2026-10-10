"""Command line interface for pipeline-post."""

import argparse
import os
import sys

from .bitbucket import BitbucketError, fetch_builds
from .commentary import DEFAULT_SEED
from .fixtures import fixture_builds
from .render import render_page


def build_parser():
    p = argparse.ArgumentParser(
        prog="pipeline-post",
        description="Bitbucket Pipelines results as a vintage horse-racing sports page.",
    )
    p.add_argument("--demo", action="store_true",
                   help="render from fixture data instead of the Bitbucket API")
    p.add_argument("--workspace",
                   help="Bitbucket workspace (required unless --demo)")
    p.add_argument("--repo",
                   help="repository slug (required unless --demo)")
    p.add_argument("-o", "--output", default="pipeline-post.html",
                   help="output file, or - for stdout (default: pipeline-post.html)")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED,
                   help="RNG seed for commentary (default: %(default)s)")
    p.add_argument("--limit", type=int, default=12,
                   help="how many recent builds to include (default: %(default)s)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.demo:
        builds = fixture_builds()
        page = render_page(builds, edition="Demo edition", demo=True, seed=args.seed)
    else:
        if not args.workspace or not args.repo:
            print("pipeline-post: --workspace and --repo are required "
                  "(or use --demo)", file=sys.stderr)
            return 2
        try:
            builds = fetch_builds(args.workspace, args.repo,
                                   limit=args.limit)
        except BitbucketError as exc:
            print("pipeline-post: %s" % exc, file=sys.stderr)
            return 1
        if not builds:
            print("pipeline-post: no finished builds found for %s/%s"
                  % (args.workspace, args.repo), file=sys.stderr)
            return 1
        page = render_page(
            builds,
            edition="%s/%s" % (args.workspace, args.repo),
            demo=False,
            seed=args.seed,
        )

    if args.output == "-":
        sys.stdout.write(page)
    else:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(page)
        print("wrote %s" % args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
