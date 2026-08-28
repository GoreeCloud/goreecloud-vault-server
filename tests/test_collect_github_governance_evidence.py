import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "collect-github-governance-evidence.py"
spec = importlib.util.spec_from_file_location("governance_collector", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class FakeClient:
    def __init__(self, overrides=None):
        self.responses = {
            "/repos/GoreeCloud/goreecloud-vault-server/branches/main/protection": (
                200,
                {
                    "required_status_checks": {"checks": [{"context": "GoreeVault CI"}], "contexts": []},
                    "required_pull_request_reviews": {
                        "require_code_owner_reviews": True,
                        "required_approving_review_count": 1,
                    },
                },
            ),
            "/repos/GoreeCloud/goreecloud-vault-server/environments/release": (
                200,
                {
                    "protection_rules": [
                        {
                            "type": "required_reviewers",
                            "reviewers": [{"type": "User", "reviewer": {"login": "reviewer"}}],
                            "prevent_self_review": True,
                        }
                    ]
                },
            ),
            "/repos/GoreeCloud/goreecloud-vault-server/actions/permissions/workflow": (
                200,
                {
                    "default_workflow_permissions": "read",
                    "can_approve_pull_request_reviews": False,
                },
            ),
            "/repos/GoreeCloud/goreecloud-vault-server/vulnerability-alerts": (204, None),
            "/repos/GoreeCloud/goreecloud-vault-server": (
                200,
                {
                    "security_and_analysis": {
                        "secret_scanning": {"status": "enabled"},
                        "secret_scanning_push_protection": {"status": "enabled"},
                    }
                },
            ),
            "/repos/GoreeCloud/goreecloud-vault-server/private-vulnerability-reporting": (
                200,
                {"enabled": True},
            ),
        }
        if overrides:
            self.responses.update(overrides)

    def get(self, path, **_kwargs):
        if path not in self.responses:
            raise AssertionError(f"unexpected path: {path}")
        return self.responses[path]


class GovernanceCollectorTests(unittest.TestCase):
    def collect(self, overrides=None):
        return module.collect(
            FakeClient(overrides),
            "GoreeCloud/goreecloud-vault-server",
            "main",
            "release",
        )

    def test_complete_governance_state_passes(self):
        result = self.collect()
        for key in (
            "main_protected",
            "required_checks_enforced",
            "required_approval_enforced",
            "codeowners_review_enforced",
            "release_environment_protected",
            "release_reviewer_required",
            "release_self_review_prevented",
            "actions_default_read_only",
            "actions_pr_approval_disabled",
            "dependabot_alerts_enabled",
        ):
            self.assertIs(result[key], True)
        self.assertEqual(result["secret_scanning"], "pass")
        self.assertEqual(result["push_protection"], "pass")
        self.assertEqual(result["private_vulnerability_reporting"], "pass")

    def test_missing_required_checks_fails(self):
        path = "/repos/GoreeCloud/goreecloud-vault-server/branches/main/protection"
        with self.assertRaises(module.EvidenceError):
            self.collect(
                {
                    path: (
                        200,
                        {
                            "required_status_checks": {"checks": [], "contexts": []},
                            "required_pull_request_reviews": {
                                "require_code_owner_reviews": True,
                                "required_approving_review_count": 1,
                            },
                        },
                    )
                }
            )

    def test_codeowner_review_must_be_enforced(self):
        path = "/repos/GoreeCloud/goreecloud-vault-server/branches/main/protection"
        with self.assertRaises(module.EvidenceError):
            self.collect(
                {
                    path: (
                        200,
                        {
                            "required_status_checks": {"checks": [{"context": "CI"}]},
                            "required_pull_request_reviews": {
                                "require_code_owner_reviews": False,
                                "required_approving_review_count": 1,
                            },
                        },
                    )
                }
            )

    def test_approval_count_must_be_positive(self):
        path = "/repos/GoreeCloud/goreecloud-vault-server/branches/main/protection"
        with self.assertRaises(module.EvidenceError):
            self.collect(
                {
                    path: (
                        200,
                        {
                            "required_status_checks": {"checks": [{"context": "CI"}]},
                            "required_pull_request_reviews": {
                                "require_code_owner_reviews": True,
                                "required_approving_review_count": 0,
                            },
                        },
                    )
                }
            )

    def test_release_self_review_must_be_prevented(self):
        path = "/repos/GoreeCloud/goreecloud-vault-server/environments/release"
        with self.assertRaises(module.EvidenceError):
            self.collect(
                {
                    path: (
                        200,
                        {
                            "protection_rules": [
                                {
                                    "type": "required_reviewers",
                                    "reviewers": [{"type": "User", "reviewer": {"login": "reviewer"}}],
                                    "prevent_self_review": False,
                                }
                            ]
                        },
                    )
                }
            )

    def test_actions_default_must_be_read_only(self):
        path = "/repos/GoreeCloud/goreecloud-vault-server/actions/permissions/workflow"
        with self.assertRaises(module.EvidenceError):
            self.collect(
                {
                    path: (
                        200,
                        {
                            "default_workflow_permissions": "write",
                            "can_approve_pull_request_reviews": False,
                        },
                    )
                }
            )

    def test_actions_cannot_approve_pull_requests(self):
        path = "/repos/GoreeCloud/goreecloud-vault-server/actions/permissions/workflow"
        with self.assertRaises(module.EvidenceError):
            self.collect(
                {
                    path: (
                        200,
                        {
                            "default_workflow_permissions": "read",
                            "can_approve_pull_request_reviews": True,
                        },
                    )
                }
            )

    def test_disabled_secret_scanning_fails(self):
        path = "/repos/GoreeCloud/goreecloud-vault-server"
        with self.assertRaises(module.EvidenceError):
            self.collect(
                {
                    path: (
                        200,
                        {
                            "security_and_analysis": {
                                "secret_scanning": {"status": "disabled"},
                                "secret_scanning_push_protection": {"status": "enabled"},
                            }
                        },
                    )
                }
            )

    def test_output_is_private_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "governance.json"
            module.write_json(path, self.collect())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(module.EvidenceError):
                module.write_json(path, self.collect())


if __name__ == "__main__":
    unittest.main()
