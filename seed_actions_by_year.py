import os
import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "progresstracker.settings")
import django

django.setup()

from tracker_app.models import Theme, Objective, Action, ActionStatus


def ensure_themes_and_objectives():
    themes = [
        ("Digital services", "Improve user-facing digital services."),
        ("Digital workforce", "Develop skills and capacity within the digital workforce."),
        ("Digital systems", "Modernise and secure the underlying digital systems."),
        ("Digital communities", "Support digital inclusion and engagement in communities."),
    ]

    objectives = []
    for title, desc in themes:
        theme, _ = Theme.objects.get_or_create(title=title)
        obj_title = f"{title} objective"
        obj, _ = Objective.objects.get_or_create(title=obj_title, defaults={"description": desc, "theme": theme})
        if obj.theme_id != theme.id:
            obj.theme = theme
            obj.save()
        objectives.append(obj)

    return objectives


def recreate_actions(year_counts=( (2024,4), (2025,2), (2026,21) )):
    # Remove any existing actions
    Action.objects.all().delete()

    objectives = ensure_themes_and_objectives()
    created = []

    # Helper to generate dates
    def dates_for_year(year, count):
        dates = []
        if year == 2026:
            # Create dates from 2026-01-01 onwards (up to today) spaced by 1 day
            start = datetime.date(2026, 1, 1)
            for i in range(count):
                dates.append(start + datetime.timedelta(days=i))
        else:
            # Spread across the year: start at Jan 15 and add 30-day steps
            start = datetime.date(year, 1, 15)
            for i in range(count):
                dates.append(start + datetime.timedelta(days=i * 30))
        return dates

    # Round-robin assign to objectives
    obj_count = len(objectives)
    idx = 0

    for year, count in year_counts:
        for d in dates_for_year(year, count):
            title = f"Auto action {year}-{len(created)+1}"
            action = Action.objects.create(
                title=title,
                small_description=f"Auto-created action for {year}",
                description=f"Auto-created action for seeding, start {d}",
                objective=objectives[idx % obj_count],
                status=ActionStatus.IN_PROGRESS,
                progress_started_at=d,
                is_approved=True,
            )
            created.append(action)
            idx += 1

    return created


if __name__ == "__main__":
    created = recreate_actions()
    print(f"Created {len(created)} actions:")
    counts = {}
    for a in created:
        counts.setdefault(a.progress_started_at.year, 0)
        counts[a.progress_started_at.year] += 1
    for year in sorted(counts):
        print(f" - {year}: {counts[year]}")
