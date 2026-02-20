from datetime import datetime, date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from tracker_app.models import Theme, Objective, Action, ActionStatus
from tracker_app.views import _build_roadmap_payload


class RoadmapPayloadTests(TestCase):
    def setUp(self):
        self.theme = Theme.objects.create(title="Test Theme")
        self.objective = Objective.objects.create(title="Test Objective", theme=self.theme)

    def _create_action(self, title, progress_started_at=None, updated_at=None, status=ActionStatus.IN_PROGRESS, is_approved=True):
        """Helper factory: create action and set timestamps deterministically.

        Note: `updated_at` is set via queryset `update()` to override auto_now.
        """
        a = Action.objects.create(
            title=title,
            small_description=title,
            description=title,
            objective=self.objective,
            status=status,
            progress_started_at=progress_started_at,
            is_approved=is_approved,
        )
        # If caller provided updated_at (a datetime), apply via update() to avoid auto_now overwrite.
        if updated_at is not None:
            Action.objects.filter(pk=a.pk).update(updated_at=updated_at)
        return Action.objects.get(pk=a.pk)

    @patch('tracker_app.views.timezone.now')
    def test_year_bounds_and_default_year_logic(self, mock_now):
        # Freeze 'now' to mid-2026 so default year becomes 2026
        mock_now.return_value = datetime(2026, 6, 1, tzinfo=timezone.utc)

        # Year below lower bound -> default used
        payload = _build_roadmap_payload('2023')
        self.assertEqual(payload['chart_year'], 2026)

        # Year above current -> default used
        payload = _build_roadmap_payload('2035')
        self.assertEqual(payload['chart_year'], 2026)

        # No year param -> default
        payload = _build_roadmap_payload(None)
        self.assertEqual(payload['chart_year'], 2026)

    @patch('tracker_app.views.timezone.now')
    def test_approved_vs_unapproved_filtering(self, mock_now):
        mock_now.return_value = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # Approved action starting 2024-02-10
        self._create_action('approved-2024', progress_started_at=date(2024, 2, 10), updated_at=datetime(2024, 2, 11))
        # Unapproved action starting 2024-02-15
        self._create_action('unapproved-2024', progress_started_at=date(2024, 2, 15), updated_at=datetime(2024, 2, 16), is_approved=False)

        payload = _build_roadmap_payload('2024')
        # Only the approved one should be counted in started_total_year
        self.assertEqual(payload['started_total_year'], 1)

    @patch('tracker_app.views.timezone.now')
    def test_started_this_year_month_indexing_and_edge_dates(self, mock_now):
        mock_now.return_value = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # First day of Jan and last day of Dec 2024
        self._create_action('start-jan-first', progress_started_at=date(2024, 1, 1), updated_at=datetime(2024, 1, 2))
        self._create_action('start-dec-last', progress_started_at=date(2024, 12, 31), updated_at=datetime(2025, 1, 1))

        payload = _build_roadmap_payload('2024')
        # Arrays must be length 12 and correct months have counts
        self.assertEqual(len(payload['chart_data_started']), 12)
        self.assertEqual(payload['chart_data_started'][0], 1)   # Jan
        self.assertEqual(payload['chart_data_started'][11], 1)  # Dec
        # Empty months zeros
        self.assertEqual(sum(payload['chart_data_started']) - 2, 0)

    @patch('tracker_app.views.timezone.now')
    def test_continued_updates_earlier_year_and_null_start(self, mock_now):
        mock_now.return_value = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # Action started in 2023, updated in Feb 2024 -> counts as continued for 2024 Feb
        self._create_action('started-2023-updated-2024', progress_started_at=date(2023, 5, 1), updated_at=datetime(2024, 2, 10))
        # Action with NULL start, updated in Mar 2024 -> counts as continued for 2024 Mar
        self._create_action('nullstart-updated-2024', progress_started_at=None, updated_at=datetime(2024, 3, 15))

        payload = _build_roadmap_payload('2024')
        # continued array length and counts at correct months
        self.assertEqual(len(payload['chart_data_continued']), 12)
        self.assertEqual(payload['chart_data_continued'][1], 1)  # Feb
        self.assertEqual(payload['chart_data_continued'][2], 1)  # Mar

    @patch('tracker_app.views.timezone.now')
    def test_completed_counts_grouped_by_updated_at_month(self, mock_now):
        mock_now.return_value = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # Completed in April 2024
        self._create_action('completed-apr', progress_started_at=date(2024, 4, 1), updated_at=datetime(2024, 4, 20), status=ActionStatus.COMPLETED)

        payload = _build_roadmap_payload('2024')
        self.assertEqual(payload['chart_data_completed'][3], 1)  # April (index 3)
        self.assertEqual(payload['completed_total_year'], 1)

    @patch('tracker_app.views.timezone.now')
    def test_in_progress_equals_started_plus_continued_no_double_counting(self, mock_now):
        mock_now.return_value = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # Action started in Jan 2024 and updated in Jan 2024 -> counts as started only
        self._create_action('started-and-updated-2024', progress_started_at=date(2024, 1, 5), updated_at=datetime(2024, 1, 6))
        # Action started earlier and updated in Jan 2024 -> counted as continued
        self._create_action('started-2023-updated-2024-jan', progress_started_at=date(2023, 6, 1), updated_at=datetime(2024, 1, 7))

        payload = _build_roadmap_payload('2024')
        # Jan started = 1, Jan continued = 1 -> in_progress (Jan) = 2
        self.assertEqual(payload['chart_data_started'][0], 1)
        self.assertEqual(payload['chart_data_continued'][0], 1)
        self.assertEqual(payload['chart_data_in_progress'][0], 2)

    @patch('tracker_app.views.timezone.now')
    def test_cross_year_behavior_started_previous_updated_current(self, mock_now):
        mock_now.return_value = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # started in 2024 but updated in 2025: should be started in 2024 and continued in 2025
        a = self._create_action('cross-year', progress_started_at=date(2024, 7, 1), updated_at=datetime(2025, 3, 5))

        payload_2024 = _build_roadmap_payload('2024')
        payload_2025 = _build_roadmap_payload('2025')

        self.assertEqual(payload_2024['chart_data_started'][6], 1)  # July 2024 started
        # In 2025, same action should appear in continued for March
        self.assertEqual(payload_2025['chart_data_continued'][2], 1)

    @patch('tracker_app.views.timezone.now')
    def test_months_with_no_data_are_zero_and_length_always_12(self, mock_now):
        mock_now.return_value = datetime(2026, 1, 1, tzinfo=timezone.utc)
        payload = _build_roadmap_payload('2024')
        self.assertEqual(len(payload['chart_data_started']), 12)
        self.assertTrue(all(isinstance(x, int) for x in payload['chart_data_started']))
        self.assertEqual(sum(payload['chart_data_started']), 0)

    @patch('tracker_app.views.timezone.now')
    def test_multiple_actions_same_month_and_edge_days_aggregation(self, mock_now):
        mock_now.return_value = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # Three actions in May 2024: first day, middle, last day
        self._create_action('may-first', progress_started_at=date(2024, 5, 1), updated_at=datetime(2024, 5, 1, 12))
        self._create_action('may-mid', progress_started_at=date(2024, 5, 15), updated_at=datetime(2024, 5, 16))
        self._create_action('may-last', progress_started_at=date(2024, 5, 31), updated_at=datetime(2024, 6, 1))

        payload = _build_roadmap_payload('2024')
        self.assertEqual(payload['chart_data_started'][4], 3)  # May index 4

    @patch('tracker_app.views.timezone.now')
    def test_admin_update_null_start_counts_as_continued(self, mock_now):
        mock_now.return_value = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # Action with NULL progress_started_at updated in 2024 => continued
        self._create_action('admin-update-nullstart', progress_started_at=None, updated_at=datetime(2024, 8, 20))

        payload = _build_roadmap_payload('2024')
        self.assertEqual(payload['chart_data_continued'][7], 1)  # Aug
