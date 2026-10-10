"""Fixture builds for --demo mode. Same data as the single-file demo page.

Each build is a dict with keys:
  n           build number (the "gate")
  branch      source branch name
  author      commit author or pipeline trigger (the "rider")
  status      "SUCCESS" or "FAILED"
  secs        duration in seconds
  failed_step None, or one of "install", "test", "deploy"
"""

FIXTURE_BUILDS = [
    {"n": 458, "branch": "main",                 "author": "ci-bot", "status": "SUCCESS", "secs": 252, "failed_step": None},
    {"n": 457, "branch": "feature/dark-mode",    "author": "priya",  "status": "FAILED",  "secs": 363, "failed_step": "test"},
    {"n": 456, "branch": "feature/dark-mode",    "author": "priya",  "status": "SUCCESS", "secs": 344, "failed_step": None},
    {"n": 455, "branch": "hotfix/login-redirect","author": "marcus", "status": "SUCCESS", "secs": 238, "failed_step": None},
    {"n": 454, "branch": "dependabot/npm-lodash","author": "ci-bot", "status": "FAILED",  "secs": 134, "failed_step": "install"},
    {"n": 453, "branch": "main",                 "author": "ci-bot", "status": "SUCCESS", "secs": 271, "failed_step": None},
    {"n": 452, "branch": "feature/sso-login",    "author": "jen",    "status": "FAILED",  "secs": 442, "failed_step": "deploy"},
    {"n": 451, "branch": "feature/sso-login",    "author": "jen",    "status": "SUCCESS", "secs": 410, "failed_step": None},
]


def fixture_builds():
    """Return a fresh copy of the fixture builds, newest first."""
    return [dict(b) for b in FIXTURE_BUILDS]
