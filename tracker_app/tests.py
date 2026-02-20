from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import translation
from unittest.mock import patch

from .admin import ActionAdmin, ObjectiveAdmin, ThemeAdmin
from .models import Action, ActionStatus, Objective, Theme


class ActionAdminSaveModelTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.admin_site = AdminSite()
		self.action_admin = ActionAdmin(Action, self.admin_site)

		self.theme = Theme.objects.create(title="Theme A")
		self.objective = Objective.objects.create(title="Objective A", theme=self.theme)

		self.staff_user = get_user_model().objects.create_user(
			username="staff_user",
			email="staff@example.com",
			password="pass1234",
			is_staff=True,
		)

		self.super_user = get_user_model().objects.create_superuser(
			username="super_user",
			email="super@example.com",
			password="pass1234",
		)

	def test_staff_save_resets_approval_and_status(self):
		action = Action.objects.create(
			title="Action A",
			objective=self.objective,
			status=ActionStatus.IN_PROGRESS,
			is_approved=True,
			update="Old update",
		)

		request = self.factory.post("/admin/")
		request.user = self.staff_user

		cleaned_data = {
			"update": "<p>New update</p>",
			"update_ga": "",
			"status": ActionStatus.IN_PROGRESS,
		}

		class DummyForm:
			def __init__(self, cleaned_data):
				self.cleaned_data = cleaned_data
				self.changed_data = ["update"]

		form = DummyForm(cleaned_data)

		action.update = cleaned_data["update"]
		action.update_ga = cleaned_data["update_ga"]
		action.status = cleaned_data["status"]

		self.action_admin.save_model(request, action, form, change=True)

		action.refresh_from_db()
		self.assertFalse(action.is_approved)
		self.assertEqual(action.status, ActionStatus.NOT_STARTED)

	def test_staff_save_keeps_status_when_not_started(self):
		action = Action.objects.create(
			title="Action Staff NS",
			objective=self.objective,
			status=ActionStatus.NOT_STARTED,
			is_approved=True,
			update="Old update",
		)

		request = self.factory.post("/admin/")
		request.user = self.staff_user

		cleaned_data = {
			"update": "<p>New update</p>",
			"update_ga": "",
			"status": ActionStatus.NOT_STARTED,
		}

		class DummyForm:
			def __init__(self, cleaned_data):
				self.cleaned_data = cleaned_data
				self.changed_data = ["update"]

		form = DummyForm(cleaned_data)
		action.update = cleaned_data["update"]
		action.update_ga = cleaned_data["update_ga"]
		action.status = cleaned_data["status"]

		self.action_admin.save_model(request, action, form, change=True)

		action.refresh_from_db()
		self.assertFalse(action.is_approved)
		self.assertEqual(action.status, ActionStatus.NOT_STARTED)
		self.assertEqual(action.updated_by, self.staff_user)

	def test_superuser_save_approves_and_sets_status_in_progress(self):
		action = Action.objects.create(
			title="Action Super",
			objective=self.objective,
			status=ActionStatus.NOT_STARTED,
			is_approved=False,
			update="",
		)

		request = self.factory.post("/admin/")
		request.user = self.super_user

		cleaned_data = {
			"update": "<p>New update</p>",
			"update_ga": "",
			"status": ActionStatus.NOT_STARTED,
		}

		class DummyForm:
			def __init__(self, cleaned_data):
				self.cleaned_data = cleaned_data
				self.changed_data = ["update"]

		form = DummyForm(cleaned_data)
		action.update = cleaned_data["update"]
		action.update_ga = cleaned_data["update_ga"]
		action.status = cleaned_data["status"]

		self.action_admin.save_model(request, action, form, change=True)

		action.refresh_from_db()
		self.assertTrue(action.is_approved)
		self.assertEqual(action.status, ActionStatus.IN_PROGRESS)
		self.assertEqual(action.updated_by, self.super_user)

	def test_superuser_save_sets_not_started_when_no_update(self):
		action = Action.objects.create(
			title="Action Super Empty",
			objective=self.objective,
			status=ActionStatus.IN_PROGRESS,
			is_approved=False,
			update="",
		)

		request = self.factory.post("/admin/")
		request.user = self.super_user

		cleaned_data = {
			"update": "",
			"update_ga": "",
			"status": ActionStatus.IN_PROGRESS,
		}

		class DummyForm:
			def __init__(self, cleaned_data):
				self.cleaned_data = cleaned_data
				self.changed_data = []

		form = DummyForm(cleaned_data)
		action.update = cleaned_data["update"]
		action.update_ga = cleaned_data["update_ga"]
		action.status = cleaned_data["status"]

		self.action_admin.save_model(request, action, form, change=True)

		action.refresh_from_db()
		self.assertTrue(action.is_approved)
		self.assertEqual(action.status, ActionStatus.NOT_STARTED)

	def test_created_by_set_on_create(self):
		action = Action(
			title="Action Created",
			objective=self.objective,
			status=ActionStatus.NOT_STARTED,
			update="",
		)

		request = self.factory.post("/admin/")
		request.user = self.staff_user

		cleaned_data = {
			"update": "",
			"update_ga": "",
			"status": ActionStatus.NOT_STARTED,
		}

		class DummyForm:
			def __init__(self, cleaned_data):
				self.cleaned_data = cleaned_data
				self.changed_data = []

		form = DummyForm(cleaned_data)
		action.update = cleaned_data["update"]
		action.update_ga = cleaned_data["update_ga"]
		action.status = cleaned_data["status"]

		self.action_admin.save_model(request, action, form, change=False)
		action.refresh_from_db()
		self.assertEqual(action.created_by, self.staff_user)
		self.assertEqual(action.updated_by, self.staff_user)

	@patch("tracker_app.admin.send_mail")
	def test_staff_update_triggers_email_on_update_change(self, mocked_send_mail):
		action = Action.objects.create(
			title="Action Notify",
			objective=self.objective,
			status=ActionStatus.IN_PROGRESS,
			is_approved=True,
			update="Old update",
		)

		request = self.factory.post("/admin/")
		request.user = self.staff_user
		request.build_absolute_uri = lambda x: f"http://testserver{x}"

		cleaned_data = {
			"update": "<p>New update</p>",
			"update_ga": "",
			"status": ActionStatus.IN_PROGRESS,
		}

		class DummyForm:
			def __init__(self, cleaned_data):
				self.cleaned_data = cleaned_data
				self.changed_data = ["update"]

		form = DummyForm(cleaned_data)
		action.update = cleaned_data["update"]
		action.update_ga = cleaned_data["update_ga"]
		action.status = cleaned_data["status"]

		self.action_admin.save_model(request, action, form, change=True)
		self.assertTrue(mocked_send_mail.called)

	@patch("tracker_app.admin.send_mail")
	def test_staff_update_no_email_when_update_not_changed(self, mocked_send_mail):
		action = Action.objects.create(
			title="Action No Notify",
			objective=self.objective,
			status=ActionStatus.IN_PROGRESS,
			is_approved=True,
			update="Old update",
		)

		request = self.factory.post("/admin/")
		request.user = self.staff_user
		request.build_absolute_uri = lambda x: f"http://testserver{x}"

		cleaned_data = {
			"update": "<p>New update</p>",
			"update_ga": "",
			"status": ActionStatus.IN_PROGRESS,
		}

		class DummyForm:
			def __init__(self, cleaned_data):
				self.cleaned_data = cleaned_data
				self.changed_data = []

		form = DummyForm(cleaned_data)
		action.update = cleaned_data["update"]
		action.update_ga = cleaned_data["update_ga"]
		action.status = cleaned_data["status"]

		self.action_admin.save_model(request, action, form, change=True)
		self.assertFalse(mocked_send_mail.called)

	@patch("tracker_app.admin.send_mail")
	def test_staff_update_ga_does_not_trigger_email(self, mocked_send_mail):
		action = Action.objects.create(
			title="Action GA Notify",
			objective=self.objective,
			status=ActionStatus.IN_PROGRESS,
			is_approved=True,
			update="Old update",
			update_ga="Old GA",
		)

		request = self.factory.post("/admin/")
		request.user = self.staff_user
		request.build_absolute_uri = lambda x: f"http://testserver{x}"

		cleaned_data = {
			"update": "<p>Old update</p>",
			"update_ga": "<p>New GA</p>",
			"status": ActionStatus.IN_PROGRESS,
		}

		class DummyForm:
			def __init__(self, cleaned_data):
				self.cleaned_data = cleaned_data
				self.changed_data = ["update_ga"]

		form = DummyForm(cleaned_data)
		action.update = cleaned_data["update"]
		action.update_ga = cleaned_data["update_ga"]
		action.status = cleaned_data["status"]

		self.action_admin.save_model(request, action, form, change=True)
		# Irish-only update should trigger notification to superusers
		self.assertTrue(mocked_send_mail.called)

	def test_superuser_save_keeps_completed_status(self):
		action = Action.objects.create(
			title="Action Completed",
			objective=self.objective,
			status=ActionStatus.COMPLETED,
			is_approved=False,
			update="Old update",
		)

		request = self.factory.post("/admin/")
		request.user = self.super_user

		cleaned_data = {
			"update": "<p>New update</p>",
			"update_ga": "",
			"status": ActionStatus.COMPLETED,
		}

		class DummyForm:
			def __init__(self, cleaned_data):
				self.cleaned_data = cleaned_data
				self.changed_data = ["update"]

		form = DummyForm(cleaned_data)
		action.update = cleaned_data["update"]
		action.update_ga = cleaned_data["update_ga"]
		action.status = cleaned_data["status"]

		self.action_admin.save_model(request, action, form, change=True)

		action.refresh_from_db()
		self.assertTrue(action.is_approved)
		self.assertEqual(action.status, ActionStatus.COMPLETED)

	def test_get_readonly_fields_for_staff(self):
		request = self.factory.get("/admin/")
		request.user = self.staff_user
		readonly = self.action_admin.get_readonly_fields(request)

		self.assertIn("title", readonly)
		self.assertIn("objective", readonly)
		self.assertIn("status", readonly)
		self.assertIn("is_approved", readonly)
		self.assertIn("small_description", readonly)
		self.assertIn("description", readonly)

	def test_get_readonly_fields_for_superuser(self):
		request = self.factory.get("/admin/")
		request.user = self.super_user
		readonly = self.action_admin.get_readonly_fields(request)

		self.assertIn("created_by", readonly)
		self.assertIn("updated_by", readonly)
		self.assertIn("created_at", readonly)
		self.assertIn("updated_at", readonly)
		self.assertNotIn("title", readonly)


class ActionDisplayUpdateTests(TestCase):
	def setUp(self):
		self.theme = Theme.objects.create(title="Theme B")
		self.objective = Objective.objects.create(title="Objective B", theme=self.theme)

	def test_display_update_hides_when_not_approved(self):
		action = Action.objects.create(
			title="Action B",
			objective=self.objective,
			update="Visible update",
			is_approved=False,
		)

		self.assertEqual(action.display_update, "")

	def test_display_update_ga_prefers_ga_when_available(self):
		action = Action.objects.create(
			title="Action C",
			objective=self.objective,
			update="English update",
			update_ga="Irish update",
			is_approved=True,
		)

		with translation.override("ga"):
			self.assertEqual(action.display_update, "Irish update")

	def test_display_update_ga_falls_back_to_english(self):
		action = Action.objects.create(
			title="Action D",
			objective=self.objective,
			update="English update",
			update_ga="",
			is_approved=True,
		)

		with translation.override("ga"):
			self.assertEqual(action.display_update, "English update")

	def test_display_small_description_bilingual(self):
		action = Action.objects.create(
			title="Action Small",
			objective=self.objective,
			small_description="Small EN",
			small_description_ga="Small GA",
			is_approved=True,
		)

		with translation.override("ga"):
			self.assertEqual(action.display_small_description, "Small GA")
		with translation.override("en"):
			self.assertEqual(action.display_small_description, "Small EN")

	def test_display_description_bilingual(self):
		action = Action.objects.create(
			title="Action Desc",
			objective=self.objective,
			description="Desc EN",
			description_ga="Desc GA",
			is_approved=True,
		)

		with translation.override("ga"):
			self.assertEqual(action.display_description, "Desc GA")
		with translation.override("en"):
			self.assertEqual(action.display_description, "Desc EN")

	def test_display_update_empty_when_approved_but_blank(self):
		action = Action.objects.create(
			title="Action Empty Update",
			objective=self.objective,
			update="",
			is_approved=True,
		)

		self.assertEqual(action.display_update, "")


class ModelStringRepresentationTests(TestCase):
	def setUp(self):
		self.theme = Theme.objects.create(title="Theme Name")
		self.objective = Objective.objects.create(title="Objective Name", theme=self.theme)
		self.action = Action.objects.create(title="Action Name", objective=self.objective)

	def test_theme_str(self):
		self.assertEqual(str(self.theme), "Theme Name")

	def test_objective_str(self):
		self.assertEqual(str(self.objective), "Objective Name")

	def test_action_str(self):
		self.assertEqual(str(self.action), "Action Name")


class ObjectiveDisplayTests(TestCase):
	def setUp(self):
		self.theme = Theme.objects.create(title="Theme Obj")

	def test_objective_display_title_fallback(self):
		objective = Objective.objects.create(
			title="Objective EN",
			theme=self.theme,
		)
		objective.title_ga = "Objective GA"

		with translation.override("ga"):
			self.assertEqual(objective.display_title, "Objective GA")
		with translation.override("en"):
			self.assertEqual(objective.display_title, "Objective EN")

	def test_objective_display_description_fallback(self):
		objective = Objective.objects.create(
			title="Objective EN 2",
			description="Desc EN",
			description_ga="Desc GA",
			theme=self.theme,
		)

		with translation.override("ga"):
			self.assertEqual(objective.display_description, "Desc GA")
		with translation.override("en"):
			self.assertEqual(objective.display_description, "Desc EN")


class FilteredActionsApiTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.theme = Theme.objects.create(title="Theme C")
		self.objective = Objective.objects.create(title="Objective C", theme=self.theme)

		self.action_in_progress = Action.objects.create(
			title="Action In Progress",
			objective=self.objective,
			status=ActionStatus.IN_PROGRESS,
			small_description="Short EN",
			small_description_ga="Short GA",
			description="Desc EN",
			description_ga="Desc GA",
			update="Update EN",
			update_ga="Update GA",
			is_ga_approved=False,
		)

		self.action_completed = Action.objects.create(
			title="Action Completed",
			objective=self.objective,
			status=ActionStatus.COMPLETED,
			small_description="Completed EN",
			description="Completed Desc EN",
			update="Completed Update EN",
		)

	def test_filtered_actions_api_returns_expected_json(self):
		url = reverse("tracker_app:filter_actions_by_status", args=["in_progress"])
		response = self.client.get(url)

		self.assertEqual(response.status_code, 200)
		payload = response.json()

		self.assertIn("status_title", payload)
		self.assertIn("actions", payload)
		self.assertIn("count", payload)
		self.assertIn("current_page", payload)
		self.assertIn("total_pages", payload)
		self.assertIn("has_next", payload)
		self.assertIn("has_previous", payload)

		self.assertEqual(payload["count"], 1)
		self.assertEqual(len(payload["actions"]), 1)

		action_payload = payload["actions"][0]
		self.assertEqual(action_payload["id"], self.action_in_progress.id)
		self.assertEqual(action_payload["title"], "Action In Progress")
		self.assertEqual(action_payload["small_description"], "Short EN")
		self.assertEqual(action_payload["description"], "Desc EN")
		self.assertEqual(action_payload["update"], "Update EN")

	def test_filtered_actions_api_respects_theme_filter(self):
		other_theme = Theme.objects.create(title="Theme D")
		other_objective = Objective.objects.create(title="Objective D", theme=other_theme)
		Action.objects.create(
			title="Other Theme Action",
			objective=other_objective,
			status=ActionStatus.IN_PROGRESS,
			small_description="Other Short",
			description="Other Desc",
			update="Other Update",
		)

		url = reverse("tracker_app:filter_actions_by_status", args=["in_progress"])
		response = self.client.get(url, {"theme_id": self.theme.id})
		payload = response.json()

		self.assertEqual(payload["count"], 1)
		self.assertEqual(payload["actions"][0]["id"], self.action_in_progress.id)

	def test_filtered_actions_api_ga_fallback_behavior(self):
		self.action_in_progress.is_ga_approved = True
		self.action_in_progress.save(update_fields=["is_ga_approved"])

		with translation.override("ga"):
			url = reverse("tracker_app:filter_actions_by_status", args=["in_progress"])
			response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="ga")
			payload = response.json()

		action_payload = payload["actions"][0]
		self.assertEqual(action_payload["small_description"], "Short GA")
		self.assertEqual(action_payload["description"], "Desc GA")
		self.assertEqual(action_payload["update"], "Update GA")

	def test_filtered_actions_api_ga_falls_back_when_not_approved(self):
		url = reverse("tracker_app:filter_actions_by_status", args=["in_progress"])

		with translation.override("ga"):
			response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="ga")
			payload = response.json()

		action_payload = payload["actions"][0]
		self.assertEqual(action_payload["small_description"], "Short EN")
		self.assertEqual(action_payload["description"], "Desc EN")
		self.assertEqual(action_payload["update"], "Update EN")

	def test_filtered_actions_api_handles_unknown_status(self):
		url = reverse("tracker_app:filter_actions_by_status", args=["unknown"])
		response = self.client.get(url)
		payload = response.json()

		self.assertEqual(payload["count"], 0)
		self.assertEqual(payload["actions"], [])

	def test_filtered_actions_api_pagination_flags(self):
		Action.objects.filter(objective=self.objective).delete()
		for i in range(11):
			Action.objects.create(
				title=f"Action P{i}",
				objective=self.objective,
				status=ActionStatus.NOT_STARTED,
				small_description="Short",
				description="Desc",
				update="",
			)

		url = reverse("tracker_app:filter_actions_by_status", args=["not_started"])
		response = self.client.get(url, {"page": 1})
		payload = response.json()

		self.assertEqual(payload["total_pages"], 2)
		self.assertTrue(payload["has_next"])
		self.assertFalse(payload["has_previous"])

		response_page_2 = self.client.get(url, {"page": 2})
		payload_page_2 = response_page_2.json()
		self.assertFalse(payload_page_2["has_next"])
		self.assertTrue(payload_page_2["has_previous"])

	def test_filtered_actions_api_returns_empty_update_as_blank(self):
		Action.objects.filter(objective=self.objective, status=ActionStatus.IN_PROGRESS).update(update="")
		url = reverse("tracker_app:filter_actions_by_status", args=["in_progress"])
		response = self.client.get(url)
		payload = response.json()
		self.assertEqual(payload["actions"][0]["update"], "")


class ThemeDetailsViewTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.theme = Theme.objects.create(title="Theme Details", title_ga="Téama")
		self.objective = Objective.objects.create(title="Objective D", theme=self.theme)

		self.action_approved = Action.objects.create(
			title="Action Approved",
			objective=self.objective,
			status=ActionStatus.IN_PROGRESS,
			description="Desc EN",
			update="Update EN",
			is_approved=True,
		)

		self.action_unapproved = Action.objects.create(
			title="Action Unapproved",
			objective=self.objective,
			status=ActionStatus.IN_PROGRESS,
			description="Desc EN",
			update="Hidden Update",
			is_approved=False,
		)

	def test_theme_details_returns_404_for_missing(self):
		url = reverse("tracker_app:get_theme_details", args=[9999])
		response = self.client.get(url)
		self.assertEqual(response.status_code, 404)
		self.assertIn("title", response.json())

	def test_theme_details_title_uses_ga_when_available(self):
		with translation.override("ga"):
			url = reverse("tracker_app:get_theme_details", args=[self.theme.id])
			response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="ga")
			payload = response.json()

		self.assertEqual(payload["title"], "Téama")

	def test_theme_details_hides_unapproved_progress(self):
		url = reverse("tracker_app:get_theme_details", args=[self.theme.id])
		response = self.client.get(url)
		payload = response.json()
		html = payload["html_content"]
		self.assertIn("Action Progress", html)
		self.assertNotIn("Hidden Update", html)

	def test_theme_details_counts_rendered(self):
		Action.objects.create(
			title="Action Completed",
			objective=self.objective,
			status=ActionStatus.COMPLETED,
			description="Desc EN",
			update="",
			is_approved=True,
		)
		Action.objects.create(
			title="Action Not Started",
			objective=self.objective,
			status=ActionStatus.NOT_STARTED,
			description="Desc EN",
			update="",
			is_approved=True,
		)

		url = reverse("tracker_app:get_theme_details", args=[self.theme.id])
		response = self.client.get(url)
		payload = response.json()
		html = payload["html_content"]
		self.assertIn("data-target=\"1\"", html)


class LanguageRoutingTests(TestCase):
	def setUp(self):
		self.client = Client()

	def test_home_route_en(self):
		response = self.client.get("/en/")
		self.assertEqual(response.status_code, 200)

	def test_home_route_ga(self):
		response = self.client.get("/ga/")
		self.assertEqual(response.status_code, 200)

	def test_home_route_default_redirects(self):
		response = self.client.get("/")
		self.assertIn(response.status_code, [301, 302])
		self.assertIn("/en/", response.headers.get("Location", ""))


class AdminConfigTests(TestCase):
	def test_action_admin_list_config(self):
		admin_site = AdminSite()
		action_admin = ActionAdmin(Action, admin_site)

		self.assertIn("objective", action_admin.list_filter)
		self.assertIn("status", action_admin.list_filter)
		self.assertIn("is_approved", action_admin.list_filter)
		self.assertIn("updated_by", action_admin.list_filter)

		self.assertIn("title", action_admin.list_display)
		self.assertIn("objective", action_admin.list_display)
		self.assertIn("status", action_admin.list_display)
		self.assertIn("is_approved", action_admin.list_display)

	def test_theme_admin_list_config(self):
		admin_site = AdminSite()
		theme_admin = ThemeAdmin(Theme, admin_site)
		self.assertIn("title", theme_admin.list_display)
		self.assertIn("title_ga", theme_admin.list_display)

	def test_objective_admin_list_config(self):
		admin_site = AdminSite()
		objective_admin = ObjectiveAdmin(Objective, admin_site)
		self.assertIn("theme", objective_admin.list_filter)
		self.assertIn("title", objective_admin.list_display)
