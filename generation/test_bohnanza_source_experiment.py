from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import generation.run_bohnanza_source_experiment as experiment
from generation.run_bohnanza_source_experiment import GAME_DIR, MANIFEST_PATH, load_manifest

ROOT = Path(__file__).resolve().parents[1]


class BohnanzaSourceExperimentTests(unittest.TestCase):
    def load(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_clean_component_json_is_internally_consistent(self):
        data = self.load(GAME_DIR / "game_components.json")
        self.assertEqual((GAME_DIR / "game_components.json").read_bytes(), (ROOT / "bohnanza_bohnenwerte.json").read_bytes())
        self.assertEqual(data["titel"], "Bohnanza – Bohnen und Erntewerte")
        self.assertEqual(sum(bean["anzahl_karten"] for bean in data["bohnen"]), 157)
        self.assertEqual(data["gesamtzahl_aufgelisteter_bohnenkarten"], 157)
        self.assertEqual(data["bohnen"][8]["name"], "Kaffeebohne")
        self.assertIn("nicht immer alle Sorten gleichzeitig", data["hinweise"][4])

    def test_mutated_json_contains_only_preregistered_logical_mutations(self):
        clean = self.load(GAME_DIR / "game_components.json")
        mutated = self.load(GAME_DIR / "variants/components_mutated.json")
        self.assertEqual(mutated["bohnen"][11]["ernte"][0]["gold"], 2)
        self.assertEqual([entry["ab_bohnen"] for entry in mutated["bohnen"][9]["ernte"]], [2, 4, 6, 8])
        self.assertIn("alle 157", mutated["hinweise"][4])
        restored = json.loads(json.dumps(mutated))
        restored["bohnen"][11]["ernte"] = clean["bohnen"][11]["ernte"]
        restored["bohnen"][9]["ernte"] = clean["bohnen"][9]["ernte"]
        restored["hinweise"][4] = clean["hinweise"][4]
        self.assertEqual(restored, clean)

    @unittest.skipUnless(shutil.which("pdftotext"), "pdftotext unavailable")
    def test_mutated_pdf_contains_exact_preregistered_rules(self):
        text = subprocess.check_output(
            ["pdftotext", "-layout", str(GAME_DIR / "variants/game_rules_mutated.pdf"), "-"],
            text=True,
            errors="replace",
        )
        self.assertIn("Du darfst nur als aktiver Spieler deine Bohnenfelder abernten.", text)
        self.assertIn("zieht nur der aktive Spieler drei Karten", text)
        self.assertIn("Karten jederzeit sortieren.", text)
        self.assertNotIn("Karten nicht sortieren.", text)
        self.assertNotIn("nicht der aktive Spieler bist", text)

    def test_manifest_hashes_and_round_robin_order_are_frozen(self):
        manifest = load_manifest()
        self.assertEqual(len(manifest["sequential_order"]), 12)
        self.assertEqual(manifest["sequential_order"][:4], ["pdf_only_1", "json_clean_1", "json_mutated_1", "pdf_mutated_1"])
        for condition in manifest["conditions"].values():
            for source in condition["sources"]:
                path = GAME_DIR / source["path"]
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), source["sha256"])

    def test_isolation_audit_rejects_repository_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            events = Path(directory) / "events.jsonl"
            events.write_text('{"command":"python local_check.py"}\n', encoding="utf-8")
            experiment.audit_isolation(events)
            events.write_text(json.dumps({"command": str(ROOT / "checks/run_scenarios.py")}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "isolation audit"):
                experiment.audit_isolation(events)

    def test_generation_and_judges_are_strictly_sequential_and_resumable(self):
        manifest = load_manifest()
        state = {"schema_version": 1, "completed": [], "judged": [], "failed": [], "updated_at": None}
        generated = []
        with patch.object(experiment, "progress", return_value=state), patch.object(experiment, "save_progress"), patch.object(
            experiment, "generate_one", side_effect=lambda run_id, condition: generated.append(run_id)
        ):
            self.assertEqual(experiment.generate(manifest, 5), 0)
        self.assertEqual(generated, manifest["sequential_order"][:5])
        self.assertEqual(state["completed"], generated)

        judged = []
        with patch.object(experiment, "progress", return_value=state), patch.object(experiment, "save_progress"), patch.object(
            experiment, "judge_one", side_effect=lambda run_id, index: judged.append(f"{run_id}_judge_{index}")
        ):
            self.assertEqual(experiment.run_judges(manifest, 5), 0)
        self.assertEqual(judged, [
            "pdf_only_1_judge_1", "pdf_only_1_judge_2", "pdf_only_1_judge_3",
            "json_clean_1_judge_1", "json_clean_1_judge_2",
        ])

    def test_every_preregistered_mutation_has_a_frozen_scenario(self):
        suite = self.load(ROOT / "checks/scenarios/bohnanza.json")
        registry = self.load(ROOT / "checks/mutations/bohnanza_source_experiment.json")
        scenario_ids = {scenario["id"] for scenario in suite["scenarios"]}
        self.assertEqual(len(registry["mutations"]), 6)
        for mutation in registry["mutations"]:
            self.assertTrue(set(mutation["scenarios"]) <= scenario_ids, mutation["id"])


if __name__ == "__main__":
    unittest.main()
