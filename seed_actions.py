import os
import sys
import shutil
import datetime

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progresstracker.settings')
import django
django.setup()

from tracker_app.models import Theme, Objective, Action, ActionStatus


def backup_db():
    src = os.path.join(PROJECT_ROOT, 'db.sqlite3')
    if not os.path.exists(src):
        print('No db.sqlite3 found to back up')
        return None
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(PROJECT_ROOT, f'db.sqlite3.backup_{ts}')
    shutil.copy2(src, dest)
    print('Created DB backup:', os.path.basename(dest))
    return dest


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


def recreate_actions(year_counts=((2024, 4), (2025, 2), (2026, 21))):
    # destructive: remove existing actions
    print('Deleting existing Action rows...')
    Action.objects.all().delete()

    objectives = ensure_themes_and_objectives()
    created = []

    def dates_for_year(year, count):
        dates = []
        if year == 2026:
            start = datetime.date(2026, 1, 1)
            for i in range(count):
                dates.append(start + datetime.timedelta(days=i))
        else:
            start = datetime.date(year, 1, 15)
            for i in range(count):
                dates.append(start + datetime.timedelta(days=i * 30))
        return dates

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

    print(f"Created {len(created)} actions")
    return created


def make_words(count, lang='en'):
    if lang == 'en':
        base = "word"
    else:
        base = "focal"
    return ' '.join([f"{base}{i+1}" for i in range(count)])


def normalize_titles_and_texts():
    objectives = list(Objective.objects.all().order_by('id'))
    for idx, obj in enumerate(objectives, start=1):
        obj.title = f"{idx:03d}"
        obj.description = make_words(15, 'en')
        obj.description_ga = make_words(15, 'ga')
        obj.save()

    actions = list(Action.objects.all().order_by('id'))
    for idx, act in enumerate(actions, start=1):
        act.title = f"MCC_ACT_{idx:03d}"
        act.small_description = make_words(10, 'en')
        act.small_description_ga = make_words(10, 'ga')
        act.save()

    print(f"Normalized {len(objectives)} objectives and {len(actions)} actions")


OBJ_DESC = (
    "The primary objective of this action is to revolutionize the way Meath County Council interacts with its citizens through a unified digital ."
)

ACTION_SHORT = "This is a ten word short description for testing purposes."


def force_numeric_objective_titles():
    objs = list(Objective.objects.all().order_by('id'))
    for idx, o in enumerate(objs, start=1):
        o.title = f"{idx:03d}"
        o.description = OBJ_DESC
        o.description_ga = OBJ_DESC
        o.save()

    actions = list(Action.objects.all().order_by('id'))
    for a in actions:
        a.small_description = ACTION_SHORT
        a.small_description_ga = ACTION_SHORT
        a.save()

    print(f"Forced numeric titles for {len(objs)} objectives and updated {len(actions)} actions")


def ensure_ten_objectives_per_theme():
    themes = list(Theme.objects.all())
    created_total = 0
    for theme in themes:
        existing = list(theme.objectives.all().order_by('id'))
        need = 10 - len(existing)
        start_index = len(existing) + 1
        for i in range(need):
            num = start_index + i
            title = f"{theme.title} - {num:03d}"
            obj = Objective.objects.create(
                title=title,
                description=make_words(15, 'en'),
                description_ga=make_words(15, 'ga'),
                theme=theme,
            )
            created_total += 1
        print(f"Theme '{theme.title}': had {len(existing)}, created {max(0, need)} new objectives")

    print(f"Total objectives created: {created_total}")


def enrich_actions_and_create_not_started(num_not_started=10):
    sizes = [50, 100, 200, 300, 400]
    actions = list(Action.objects.all().order_by('id'))
    updated = 0

    for idx, action in enumerate(actions):
        size = sizes[idx % len(sizes)]
        en_text = ' '.join(['sample'] * size)
        ga_text = ' '.join(['samplach'] * size)

        action.description = en_text
        action.update = en_text
        action.description_ga = ga_text
        action.update_ga = ga_text
        action.save()
        updated += 1

    objectives = list(Objective.objects.all())
    if not objectives:
        theme, _ = Theme.objects.get_or_create(title='Auto Theme')
        objectives = [Objective.objects.create(title='Auto Objective', theme=theme)]

    created = 0
    for i in range(num_not_started):
        obj = objectives[i % len(objectives)]
        title = f"Seed NotStarted Action {i+1}"
        a = Action.objects.create(
            title=title,
            small_description=f"Not started action {i+1}",
            description=' '.join(['sample'] * 50),
            description_ga=' '.join(['samplach'] * 50),
            update="",
            update_ga="",
            objective=obj,
            status=ActionStatus.NOT_STARTED,
            is_approved=False,
            progress_started_at=None,
        )
        created += 1

    print(f"Updated {updated} existing actions with rich texts.")
    print(f"Created {created} NOT_STARTED actions.")


if __name__ == '__main__':
    print('Starting master seed: backing up DB...')
    backup_db()
    print('Recreating actions by year...')
    recreate_actions()
    print('Normalizing titles...')
    normalize_titles_and_texts()
    print('Forcing numeric objective titles and action short descriptions...')
    force_numeric_objective_titles()
    print('Ensuring ten objectives per theme...')
    ensure_ten_objectives_per_theme()
    print('Enriching actions with rich text and adding NOT_STARTED actions...')
    enrich_actions_and_create_not_started()
    print('Master seeding complete.')
