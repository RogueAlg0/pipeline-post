"""Bitbucket Cloud Pipelines API client. Python standard library only.

Auth is HTTP Basic with BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD
from the environment.

Field mapping notes (see README): the client normalizes each pipeline to
the build dict used by commentary and render:
  n, branch, author, status ("SUCCESS"/"FAILED"), secs, failed_step
Builds still running are skipped, since they have no final time.
"""

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API_BASE = "https://api.bitbucket.org/2.0"

WON_STATES = {"SUCCESSFUL"}
FELL_STATES = {"FAILED", "STOPPED", "ERROR"}


class BitbucketError(Exception):
    pass


def _auth_header(username, password):
    token = base64.b64encode(("%s:%s" % (username, password)).encode("utf-8")).decode("ascii")
    return "Basic " + token


def _get(url, username, password):
    req = urllib.request.Request(url, headers={
        "Authorization": _auth_header(username, password),
        "Accept": "application/json",
        "User-Agent": "pipeline-post/0.1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            detail = ""
        if exc.code == 401:
            raise BitbucketError(
                "authentication failed (401): check BITBUCKET_USERNAME "
                "and BITBUCKET_APP_PASSWORD") from exc
        if exc.code == 404:
            raise BitbucketError(
                "repository not found (404): check the workspace and repo "
                "slug, and that the credentials can see it") from exc
        raise BitbucketError("Bitbucket API error %s: %s" % (exc.code, detail)) from exc
    except urllib.error.URLError as exc:
        raise BitbucketError("could not reach Bitbucket: %s" % exc.reason) from exc


def _parse_ts(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError):
        return None


def _duration_secs(pipeline):
    secs = pipeline.get("duration_in_seconds")
    if isinstance(secs, (int, float)) and secs >= 0:
        return int(secs)
    start = _parse_ts(pipeline.get("created_on"))
    end = _parse_ts(pipeline.get("completed_on"))
    if start and end:
        return max(0, int((end - start).total_seconds()))
    return 0


def _categorize_step(name):
    low = (name or "").lower()
    if "install" in low:
        return "install"
    if "test" in low:
        return "test"
    if "deploy" in low:
        return "deploy"
    return None


def _failed_step(workspace, repo_slug, pipeline_uuid, username, password):
    """Find the first failed step of a pipeline and categorize it."""
    url = "%s/repositories/%s/%s/pipelines/%s/steps/" % (
        API_BASE,
        urllib.parse.quote(workspace, safe=""),
        urllib.parse.quote(repo_slug, safe=""),
        urllib.parse.quote(pipeline_uuid, safe=""),
    )
    try:
        data = _get(url, username, password)
    except BitbucketError:
        return None
    for step in data.get("values", []):
        state = (step.get("state") or {}).get("name", "")
        if state in FELL_STATES:
            return _categorize_step(step.get("name"))
    return None


def _normalize(pipeline):
    state = (pipeline.get("state") or {}).get("name", "")
    if state in WON_STATES:
        status = "SUCCESS"
    elif state in FELL_STATES:
        status = "FAILED"
    else:
        return None  # still running or an unknown state: skip
    target = pipeline.get("target") or {}
    branch = target.get("ref_name") or "unknown"
    creator = pipeline.get("creator") or {}
    author = creator.get("display_name") or creator.get("nickname") or "unknown"
    return {
        "n": pipeline.get("build_number", 0),
        "branch": branch,
        "author": author,
        "status": status,
        "secs": _duration_secs(pipeline),
        "failed_step": None,
        "_uuid": pipeline.get("uuid", ""),
    }


def fetch_builds(workspace, repo_slug, username=None, app_password=None, limit=12):
    """Fetch the newest finished pipeline builds, newest first.

    Raises BitbucketError with a human-readable message on any API problem.
    """
    username = username or os.environ.get("BITBUCKET_USERNAME")
    app_password = app_password or os.environ.get("BITBUCKET_APP_PASSWORD")
    if not username or not app_password:
        raise BitbucketError(
            "set BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD in the "
            "environment before fetching real pipelines")
    url = "%s/repositories/%s/%s/pipelines/?pagelen=%d" % (
        API_BASE,
        urllib.parse.quote(workspace, safe=""),
        urllib.parse.quote(repo_slug, safe=""),
        max(limit * 2, 25),
    )
    data = _get(url, username, password)
    values = data.get("values", [])
    # Newest first, by creation time.
    values.sort(key=lambda p: p.get("created_on", ""), reverse=True)
    builds = []
    for pipeline in values:
        build = _normalize(pipeline)
        if build is None:
            continue
        builds.append(build)
        if len(builds) >= limit:
            break
    # Look up the failed step for fallen runners only.
    for build in builds:
        if build["status"] == "FAILED":
            build["failed_step"] = _failed_step(
                workspace, repo_slug, build.pop("_uuid"), username, app_password)
        else:
            build.pop("_uuid", None)
    return builds
