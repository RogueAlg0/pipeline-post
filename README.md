# The Pipeline Post

Bitbucket Pipelines results as a vintage horse-racing sports page. Builds
become racehorses named after their branches, authors become riders, and
results are reported as WON or FELL, with generated race commentary, a form
table, and a Stewards' Inquiries section for failed builds.

## Quickstart

Render the demo edition from fixture data, no credentials needed:

```
pipeline-post --demo
```

This writes `pipeline-post.html`. Use `-o -` to print to stdout instead:

```
pipeline-post --demo -o - | head -20
```

## Real usage

Set your credentials, then point at a workspace and repo slug:

```
export BITBUCKET_USERNAME=you@example.com
export BITBUCKET_APP_PASSWORD=your-app-password
pipeline-post --workspace myteam --repo myservice -o race-day.html
```

Auth is HTTP Basic with the username and app password. The `--limit`
flag controls how many recent builds appear (default 12), and `--seed`
pins the commentary RNG so a page renders identically every time.

## Bitbucket Pipelines API note

Reads the public Bitbucket Cloud REST API: the pipelines list at
`/2.0/repositories/{workspace}/{repo_slug}/pipelines/`, plus each failed
build's step list to find which step fell. Only the standard library is
used, so there are zero dependencies.

## Layout

- `pipeline_post/cli.py` argument parsing and entry point
- `pipeline_post/bitbucket.py` API client (urllib only)
- `pipeline_post/commentary.py` race-call generator with a seeded RNG
- `pipeline_post/render.py` HTML page renderer
- `pipeline_post/fixtures.py` demo fixture builds
