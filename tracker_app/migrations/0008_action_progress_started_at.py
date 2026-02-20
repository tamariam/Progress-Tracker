from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracker_app", "0007_action_description_ga_action_is_ga_approved_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="action",
            name="progress_started_at",
            field=models.DateField(
                blank=True,
                help_text="Set the date this action first moved from Inactive to In progress.",
                null=True,
                verbose_name="Progress started on",
            ),
        ),
    ]
