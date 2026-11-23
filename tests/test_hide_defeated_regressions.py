"""Regression tests for v1.0.9: duplicate boss names (issue #13) and the F8
overlay ignoring "Hide Defeated Bosses"."""
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.ui.managers.overlay_manager import OverlayManager
from src.ui.widgets.location_section import LocationSectionWidget

# Liurnia really has two Night's Cavalry with different event IDs.
LIURNIA = [
    {"id": 1039430800, "name": "Night's Cavalry", "is_defeated": False},
    {"id": 1036480800, "name": "Night's Cavalry", "is_defeated": True},
    {"id": 1, "name": "Royal Knight Loretta", "is_defeated": True},
]


class LocationSectionDuplicateNamesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt_app = QApplication.instance() or QApplication([])

    def test_header_counts_each_duplicate(self):
        widget = LocationSectionWidget("Liurnia of the Lakes", LIURNIA)
        self.assertIn("(2/3)", widget.location_name_label.text())

    def test_hide_defeated_hides_only_the_killed_duplicate(self):
        widget = LocationSectionWidget("Liurnia of the Lakes", LIURNIA)
        widget.apply_status_filter(True)
        self.assertFalse(widget.boss_table.isRowHidden(0))
        self.assertTrue(widget.boss_table.isRowHidden(1))
        self.assertTrue(widget.boss_table.isRowHidden(2))


class OverlayBossListHideDefeatedTest(unittest.TestCase):
    DATA = {
        "Limgrave": [{"name": "Margit", "is_defeated": True}],
        "Liurnia of the Lakes": LIURNIA,
    }

    def test_shows_everything_when_filter_off(self):
        html = OverlayManager._build_boss_list_html(self.DATA, False)
        self.assertIn("Limgrave (1/1)", html)
        self.assertIn("Royal Knight Loretta", html)

    def test_hides_defeated_bosses_and_finished_locations(self):
        html = OverlayManager._build_boss_list_html(self.DATA, True)
        self.assertNotIn("Limgrave", html)
        self.assertNotIn("Royal Knight Loretta", html)
        self.assertIn("Liurnia of the Lakes (2/3)", html)
        self.assertEqual(html.count("Night&#x27;s Cavalry"), 1)

    def test_all_defeated_message(self):
        data = {"Limgrave": [{"name": "Margit", "is_defeated": True}]}
        html = OverlayManager._build_boss_list_html(data, True)
        self.assertIn("All bosses defeated!", html)

    def test_no_data_message(self):
        self.assertIn("Select a character", OverlayManager._build_boss_list_html({}, True))


class OverlayRefreshOnFilterToggleTest(unittest.TestCase):
    """The cache key must include the filter, or toggling it never redraws."""

    def _manager(self, hide_defeated):
        manager = OverlayManager.__new__(OverlayManager)
        manager._mode = "full"
        manager._last_boss_list_key = None
        manager.overlay_window = MagicMock()
        manager.app = MagicMock()
        manager.app.boss_data_manager.get_boss_data_by_location.return_value = {
            "Liurnia of the Lakes": LIURNIA,
        }
        manager.app.hide_defeated_checkbox.isChecked.return_value = hide_defeated
        return manager

    def test_toggle_rebuilds_list(self):
        manager = self._manager(False)
        manager.refresh_boss_list()
        manager.refresh_boss_list()
        self.assertEqual(manager.overlay_window.set_boss_list_html.call_count, 1)

        manager.app.hide_defeated_checkbox.isChecked.return_value = True
        manager.refresh_boss_list()
        self.assertEqual(manager.overlay_window.set_boss_list_html.call_count, 2)
        html = manager.overlay_window.set_boss_list_html.call_args.args[0]
        self.assertNotIn("Royal Knight Loretta", html)


if __name__ == "__main__":
    unittest.main()
