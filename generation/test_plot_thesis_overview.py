import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plot_thesis_overview as plots


class ThesisOverviewPlotTest(unittest.TestCase):
    def test_all_curated_results_render(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(plots, "PLOTS_ROOT", Path(directory)):
            plots.main()
            overview = Path(directory) / "overview"
            for name in ("evidence_profiles.png", "intervention_deltas.png"):
                self.assertGreater((overview / name).stat().st_size, 10_000)
            for relative in (*plots.GAME_REL.values(), plots.ABALONE_V2_REL):
                self.assertGreater((Path(directory) / relative / "evidence_profile.png").stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()
