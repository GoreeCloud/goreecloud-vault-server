#!/usr/bin/env python3
"""Collect the Stable governance evidence object from GitHub without mutating settings."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EvidenceError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: str, api_url: str = "https://api.github.com") -> None:
        if not token:
            raise EvidenceError("a GitHub token is required")
        self.token = token
        self.api_url = api_url.rstrip("/")

    def get(self, path: str, *, accept: str = "application/vnd.github+json") -> tuple[int, Any]:
        request = urllib.request.Request(
            f"{self.api_url}{path}",
            headers={
                "Accept": accept,
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2026-03-10",
                "User-Agent": "goreecloud-vault-server-governance-evidence",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read()
                return response.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            detail = raw.decode("utf-8", errors="replace")[:500] if raw else ""
            raise EvidenceError(f"GitHub API {path} returned HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise EvidenceError(f"GitHub API request failed for {path}: {exc.reason}") from exc


def require_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{field} must be an object")
    return value


def require_enabled_status(value: Any, field: str) -> str:
    mapping = require_mapping(value, field)
    status = mapping.get("status")
    if status == "enabled":
        return "pass"
    if status == "disabled":
        raise EvidenceError(f"{field} is disabled")
    raise EvidenceError(f"{field} status is unavailable or unknown")


def collect(client: Any, repository: str, branch: str, release_environment: str) -> dict[str, Any]:
    if repository.count("/") != 1:
        raise EvidenceError("repository must use owner/name form")

    _, protection_raw = client.get(f"/repos/{repository}/branches/{branch}/protection")
    protection = require_mapping(protection_raw, "branch_protection")

    required_status = require_mapping(protection.get("required_status_checks"), "required_status_checks")
    checks = required_status.get("checks")
    contexts = required_status.get("contexts")
    if not bool(checks) and not bool(contexts):
        raise EvidenceError("branch protection has no required status checks")

    pr_reviews = require_mapping(
        protection.get("required_pull_request_reviews"), "required_pull_request_reviews"
    )
    if pr_reviews.get("require_code_owner_reviews") is not True:
        raise EvidenceError("CODEOWNERS review is not required by branch protection")
    approval_count = pr_reviews.get("required_approving_review_count")
    if not isinstance(approval_count, int) or approval_count < 1:
        raise EvidenceError("branch protection does not require an approving review")

    _, environment_raw = client.get(f"/repos/{repository}/environments/{release_environment}")
    environment = require_mapping(environment_raw, "release_environment")
    rules = environment.get("protection_rules")
    if not isinstance(rules, list):
        raise EvidenceError("release environment protection rules are unavailable")

    reviewer_rule = next(
        (rule for rule in rules if isinstance(rule, dict) and rule.get("type") == "required_reviewers"),
        None,
    )
    if not isinstance(reviewer_rule, dict):
        raise EvidenceError("release environment does not require reviewers")
    reviewers = reviewer_rule.get("reviewers")
    if not isinstance(reviewers, list) or not reviewers:
        raise EvidenceError("release environment has no configured reviewer")
    if reviewer_rule.get("prevent_self_review") is not True:
        raise EvidenceError("release environment does not prevent self-review")

    _, actions_raw = client.get(f"/repos/{repository}/actions/permissions/workflow")
    actions = require_mapping(actions_raw, "actions_workflow_permissions")
    if actions.get("default_workflow_permissions") != "read":
        raise EvidenceError("default GitHub Actions workflow permissions are not read-only")
    if actions.get("can_approve_pull_request_reviews") is not False:
        raise EvidenceError("GitHub Actions can approve pull request reviews")

    status, _ = client.get(f"/repos/{repository}/vulnerability-alerts")
    if status != 204:
        raise EvidenceError("Dependabot vulnerability-alert state did not return enabled status")

    _, repository_raw = client.get(f"/repos/{repository}")
    repository_data = require_mapping(repository_raw, "repository")
    security = require_mapping(repository_data.get("security_and_analysis"), "security_and_analysis")
    secret_scanning = require_enabled_status(security.get("secret_scanning"), "secret_scanning")
    push_protection = require_enabled_status(
        security.get("secret_scanning_push_protection"), "secret_scanning_push_protection"
    )

    _, private_reporting_raw = client.get(f"/repos/{repository}/private-vulnerability-reporting")
    private_reporting = require_mapping(private_reporting_raw, "private_vulnerability_reporting")
    if private_reporting.get("enabled") is not True:
        raise EvidenceError("private vulnerability reporting is disabled")

    return {
        "verified_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "main_protected": True,
        "required_checks_enforced": True,
        "required_approval_enforced": True,
        "codeowners_review_enforced": True,
        "release_environment_protected": True,
        "release_reviewer_required": True,
        "release_self_review_prevented": True,
        "actions_default_read_only": True,
        "actions_pr_approval_disabled": True,
        "dependabot_alerts_enabled": True,
        "secret_scanning": secret_scanning,
        "push_protection": push_protection,
        "private_vulnerability_reporting": "pass",
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    if path.exists():
        raise EvidenceError(f"refusing to overwrite existing evidence file: {path}")
    if path.is_symlink():
        raise EvidenceError(f"refusing symbolic-link output path: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--branch", default="main")
    parser.add_argument("--release-environment", default="release")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    try:
        token = os.environ.get(args.token_env, "")
        client = GitHubClient(token)
        evidence = collect(client, args.repository, args.branch, args.release_environment)
        write_json(args.output, evidence)
    except EvidenceError as exc:
        print(f"governance evidence collection failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
