from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail

from tracker_app.models import Theme, Objective, Action, ActionStatus


class AdminIntegrationTests(TestCase):
    def setUp(self):
        # Users
        User = get_user_model()
        self.superuser = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        self.staff = User.objects.create_user('staff', 'staff@example.com', 'pass', is_staff=True)

        # Content
        self.theme = Theme.objects.create(title='Int Test Theme')
        self.obj = Objective.objects.create(title='Int Obj', theme=self.theme)

        # Action
        self.action = Action.objects.create(
            title='Integration Action',
            small_description='s',
            description='d',
            objective=self.obj,
            status=ActionStatus.NOT_STARTED,
            is_approved=False,
        )

        self.client = Client()

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', EMAIL_FAIL_SILENTLY=False)
    def test_staff_update_triggers_notification_and_keeps_unapproved(self):
        # staff user posts an update via admin change form
        self.client.force_login(self.staff)
        url = reverse('admin:tracker_app_action_change', args=[self.action.pk])

        data = {
            'title': self.action.title,
            'small_description': self.action.small_description,
            'description': self.action.description,
            'update': '<p>New update</p>',
            'update_ga': '',
            'objective': self.obj.pk,
            'status': ActionStatus.IN_PROGRESS,
            '_save': 'Save'
        }

        resp = self.client.post(url, data, follow=True)
        self.action.refresh_from_db()

        # Staff edits should leave is_approved False
        self.assertFalse(self.action.is_approved)

        # Notification should have been sent to superusers (locmem backend)
        self.assertGreaterEqual(len(mail.outbox), 1)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_superuser_save_approves_and_sets_in_progress(self):
        self.client.force_login(self.superuser)
        url = reverse('admin:tracker_app_action_change', args=[self.action.pk])

        data = {
            'title': self.action.title,
            'small_description': self.action.small_description,
            'description': self.action.description,
            'update': '<p>Super update</p>',
            'update_ga': '',
            'objective': self.obj.pk,
            'status': ActionStatus.NOT_STARTED,
            '_save': 'Save'
        }

        resp = self.client.post(url, data, follow=True)
        self.action.refresh_from_db()

        # Superuser saves should approve
        self.assertTrue(self.action.is_approved)
        # Since update provided and status wasn't COMPLETED, status becomes IN_PROGRESS
        self.assertEqual(self.action.status, ActionStatus.IN_PROGRESS)
