import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('resource_plot', Path(__file__).with_name('plot_resources.py'))
plot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plot)


class PlotChecks(unittest.TestCase):
    def test_missing_process_row_and_long_gap_break_lines(self):
        rows = [{'sequence': i, 'elapsedSeconds': t, 'process': None if i == 1 else {'rssBytes': i + 1}} for i, t in enumerate([0, 15, 30, 90, 105])]
        parts = plot.segments(rows, 'process', 'rssBytes', 15, 4)
        self.assertEqual([len(p) for p in parts], [1, 1, 2])

    def test_sparse_disk_scan_is_continuous_but_missing_scheduled_scan_breaks(self):
        rows = [{'sequence': i, 'elapsedSeconds': i * 15, 'disk': {'complete': True, 'logicalBytes': i + 1} if i in [0, 4, 12] else None} for i in range(13)]
        parts = plot.segments(rows, 'disk', 'logicalBytes', 60, 4)
        self.assertEqual([len(p) for p in parts], [2, 1])

    def test_incomplete_scan_never_plotted_as_zero(self):
        rows = [{'sequence': i * 4, 'elapsedSeconds': i * 60, 'disk': {'complete': i != 1, 'logicalBytes': 100}} for i in range(3)]
        self.assertEqual([len(p) for p in plot.segments(rows, 'disk', 'logicalBytes', 60, 4)], [1, 1])


if __name__ == '__main__':
    unittest.main()
