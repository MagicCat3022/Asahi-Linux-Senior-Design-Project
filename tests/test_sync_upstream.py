"""Exercise the sync shell against a fake GitHub API; never change remote refs."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
BEFORE = "1" * 40
AFTER = "2" * 40
CONCURRENT = "3" * 40

FAKE_GH = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

state_path = Path(os.environ["SYNC_TEST_STATE"])
state = json.loads(state_path.read_text())
args = sys.argv[1:]
state["calls"].append(args)

def finish(output, code=0):
    state_path.write_text(json.dumps(state))
    print(output)
    sys.exit(code)

endpoint = args[1]
if endpoint == "graphql":
    fields = dict(args[i + 1].split("=", 1) for i, arg in enumerate(args) if arg == "-f")
    assert fields["repository"] == "repository-node-id"
    assert fields["ref"] == "refs/heads/" + os.environ["SYNC_BRANCH"]
    assert "beforeOid: $before" in fields["query"]
    assert "afterOid: $after" in fields["query"]
    assert "force: true" in fields["query"]
    if state["scenario"] == "concurrent":
        state["target"] = "3" * 40
    if state["scenario"] == "denied":
        finish("gh: protected branch or insufficient permissions", 1)
    if fields["before"] != state["target"]:
        finish("gh: beforeOid does not match current ref", 1)
    state["target"] = fields["after"]
    state["updates"] += 1
    finish('{"data":{"updateRefs":{"clientMutationId":null}}}')
elif endpoint == "repos/AsahiLinux/linux/git/ref/heads/" + os.environ["SYNC_BRANCH"]:
    if state["scenario"] == "missing_upstream":
        finish("gh: Not Found (HTTP 404)", 1)
    finish(state["upstream"])
elif endpoint == "repos/target/repo/git/ref/heads/" + os.environ["SYNC_BRANCH"]:
    if state["scenario"] == "missing_target":
        finish("gh: Not Found (HTTP 404)", 1)
    if state["scenario"] == "changed_after_update" and state["updates"]:
        state["target"] = "3" * 40
    finish(state["target"])
elif endpoint == "repos/target/repo":
    finish("repository-node-id")
else:
    finish("unexpected API call: " + repr(args), 1)
'''


class SyncUpstream(unittest.TestCase):
    def run_sync(self, scenario="diverged", branch="asahi"):
        workflow = (ROOT / ".github/workflows/sync-upstream.yml").read_text()
        script = textwrap.dedent(workflow.split("        run: |\n", 1)[1])
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            gh = directory / "gh"
            gh.write_text(FAKE_GH)
            gh.chmod(0o755)
            state_path = directory / "state.json"
            state_path.write_text(json.dumps({
                "scenario": scenario, "target": BEFORE,
                "upstream": BEFORE if scenario == "unchanged" else AFTER,
                "updates": 0, "calls": [],
            }))
            summary = directory / "summary.md"
            env = {**os.environ, "PATH": str(directory) + os.pathsep + os.environ["PATH"],
                   "SYNC_TEST_STATE": str(state_path), "SYNC_BRANCH": branch,
                   "TARGET_REPO": "target/repo", "UPSTREAM_REPO": "AsahiLinux/linux",
                   "GITHUB_STEP_SUMMARY": str(summary)}
            result = subprocess.run(["bash", "-c", script], env=env,
                                    capture_output=True, text=True)
            return (result, json.loads(state_path.read_text()),
                    summary.read_text() if summary.exists() else "")

    def test_all_mirrors_accept_rewritten_upstream_history(self):
        for branch in ("main", "fairydust", "asahi"):
            with self.subTest(branch=branch):
                result, state, summary = self.run_sync(branch=branch)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(state["target"], AFTER)
                self.assertEqual(state["updates"], 1)
                self.assertIn(BEFORE, summary)
                self.assertIn(AFTER, summary)

    def test_unchanged_mirror_still_checks_write_access(self):
        result, state, summary = self.run_sync("unchanged")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(state["updates"], 1)
        self.assertEqual(state["target"], BEFORE)
        self.assertIn("Already up to date", summary)

    def test_concurrent_update_is_preserved(self):
        result, state, summary = self.run_sync("concurrent")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(state["target"], CONCURRENT)
        self.assertEqual(state["updates"], 0)
        self.assertEqual(summary, "")

    def test_unexpected_branch_is_rejected_before_api_calls(self):
        for branch in ("project", "usb/dev", "usb/tipd-hpd-fix", "drm/dcp-hotplug", ""):
            with self.subTest(branch=branch):
                result, state, summary = self.run_sync(branch=branch)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(state["calls"], [])
                self.assertEqual(summary, "")

    def test_missing_refs_and_denied_updates_fail_without_success_summary(self):
        for scenario in ("missing_upstream", "missing_target", "denied"):
            with self.subTest(scenario=scenario):
                result, state, summary = self.run_sync(scenario)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(state["target"], BEFORE)
                self.assertEqual(state["updates"], 0)
                self.assertEqual(summary, "")

    def test_change_after_update_is_reported(self):
        result, state, summary = self.run_sync("changed_after_update")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected commit", result.stdout)
        self.assertEqual(state["target"], CONCURRENT)
        self.assertEqual(summary, "")


if __name__ == "__main__":
    unittest.main()
