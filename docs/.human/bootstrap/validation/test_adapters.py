from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ADAPTERS = HERE.parent / "library" / "adapters"
spec = importlib.util.spec_from_file_location("adapter_resolver", ADAPTERS / "resolve.py")
resolver = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(resolver)


class AdapterResolverTests(unittest.TestCase):
    def adapter(self, name: str) -> dict:
        return json.loads((ADAPTERS / name).read_text(encoding="utf-8"))

    def test_safe_default_and_high_autonomy_do_not_escalate(self):
        self.assertEqual(resolver.resolve_execution(), {"requested":"protected_manual", "source":"safe_default"})
        # Autonomy and consumption are deliberately not resolver inputs.
        self.assertEqual(resolver.resolve_preset(project="economy"), {"preset":"economy", "source":"project"})
        self.assertEqual(resolver.resolve_execution()["requested"], "protected_manual")

    def test_task_local_and_preset_precedence_are_independent(self):
        local = {"schema":resolver.OVERRIDE_SCHEMA, "profile":"protected_auto"}
        self.assertEqual(resolver.resolve_execution(local=local)["source"], "local")
        self.assertEqual(resolver.resolve_execution(task="protected_manual", local=local)["source"], "task")
        self.assertEqual(resolver.resolve_preset(task="standard", local="economy", project="economy")["source"], "task")
        self.assertEqual(resolver.parse_preset_override({"schema":resolver.PRESET_OVERRIDE_SCHEMA,"preset":"economy"}),"economy")

    def test_full_access_requires_explicit_risk_acknowledgement(self):
        with self.assertRaisesRegex(ValueError, "risk acknowledgement"):
            resolver.resolve_execution(local={"schema":resolver.OVERRIDE_SCHEMA, "profile":"full_access"})
        with self.assertRaisesRegex(ValueError, "risk acknowledgement"):
            resolver.resolve_execution(task="full_access")
        self.assertEqual(resolver.resolve_execution(task="full_access", task_risk_acknowledged=True)["requested"], "full_access")

    def test_codex_mappings_are_distinct_and_unobserved_is_not_applied(self):
        adapter = self.adapter("codex.json")
        actions = {}
        for profile in resolver.PROFILES:
            resolved = resolver.resolve_execution(task=profile, task_risk_acknowledged=profile == "full_access")
            result = resolver.map_request(adapter, "cli", resolved)
            self.assertEqual(result["status"], "supported")
            self.assertIsNone(result["effective"])
            self.assertFalse(result["applied"])
            actions[profile] = result["native_action"]
        self.assertEqual(len({json.dumps(x, sort_keys=True) for x in actions.values()}), 3)
        self.assertEqual(actions["protected_manual"]["settings_patch"]["approvals_reviewer"], "user")
        self.assertEqual(actions["protected_auto"]["settings_patch"]["approvals_reviewer"], "auto_review")
        self.assertEqual(actions["full_access"]["settings_patch"]["sandbox_mode"], "danger-full-access")

    def test_claude_auto_unknown_never_falls_through(self):
        result = resolver.map_request(self.adapter("claude-code.json"), "cli",
                                      resolver.resolve_execution(task="protected_auto"))
        self.assertEqual((result["requested"], result["effective"], result["status"]),
                         ("protected_auto", None, "unknown"))
        self.assertNotIn("dangerously-skip-permissions", result["native_action"]["cli_args"])

    def test_observation_and_managed_policy_are_reported(self):
        requested = resolver.resolve_execution(task="full_access", task_risk_acknowledged=True)
        blocked = resolver.map_request(self.adapter("codex.json"), "cli", requested,
                                       managed_policy={"allowed_profiles":["protected_manual"]})
        self.assertEqual((blocked["status"], blocked["effective"]), ("unsupported", None))
        observed = resolver.map_request(self.adapter("codex.json"), "cli", requested,
                                        observation={"status":"supported", "effective":"full_access"})
        self.assertTrue(observed["applied"])

    def test_clear_override_returns_to_safe_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / ".local" / "config" / "execution-profile.json"
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps({"schema":resolver.OVERRIDE_SCHEMA,"profile":"protected_auto"}), encoding="utf-8")
            self.assertTrue(resolver.clear_local_override(root))
            self.assertFalse(target.exists())
            self.assertEqual(resolver.resolve_execution()["requested"], "protected_manual")
            preset = root / ".local" / "config" / "preset.json"
            preset.write_text(json.dumps({"schema":resolver.PRESET_OVERRIDE_SCHEMA,"preset":"economy"}),encoding="utf-8")
            self.assertTrue(resolver.clear_local_preset(root))
            self.assertFalse(preset.exists())


if __name__ == "__main__":
    unittest.main()
