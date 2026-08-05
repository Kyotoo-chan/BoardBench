import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import plot_thesis_overview as plots


class ThesisOverviewPlotTest(unittest.TestCase):
    def test_all_curated_results_render(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(plots, "OUTPUT", Path(directory)):
            plots.main()
            for name in ("evidence_profiles.png", "intervention_deltas.png"):
                self.assertGreater((Path(directory) / name).stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()
