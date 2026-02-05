import os
import django
import random
import uuid

# 1. SETUP DJANGO
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progresstracker.settings')
django.setup()

from tracker_app.models import Theme, Objective, Action, ActionStatus

def seed():
    print("--- STEP 1: WIPING DATABASE CLEAN ---")
    Action.objects.all().delete()
    Objective.objects.all().delete()
    Theme.objects.all().delete()
    print("Database is now empty.")

    # 2. LONG TEXT FOR FULL DETAILS (Approx 150-200 words)
    mega_text = """
    The primary objective of this action is to revolutionize the way Meath County Council interacts 
    with its citizens through a unified digital portal. This project involves the integration of 
    multiple legacy back-office systems into a single, responsive web interface that adheres to the 
    highest standards of accessibility (WCAG 2.1). By implementing this strategy, we aim to reduce 
    manual processing times by approximately 40% over the next two years. Key deliverables include 
    a centralized user dashboard, real-time application tracking, and automated email notifications 
    for all planning and housing requests. Explore the draft UX here: 
    <a href="https://example.com/portal-preview" target="_blank" rel="noopener noreferrer">Portal Preview</a>. 
    You can also see the accessibility checklist at 
    <a href="https://example.com/wcag-checklist" target="_blank" rel="noopener noreferrer">WCAG Checklist</a>. 
    Furthermore, the system will undergo rigorous security audits to ensure data protection compliance. 
    We are committed to ensuring that no citizen is left behind, offering digital-first solutions while 
    maintaining essential traditional communication channels for those who require them. This long-form 
    text is specifically designed to test the vertical expansion of the modal and ensure that the 
    accordion handles large blocks of HTML content without overlapping other elements in the table view.
    """

    themes_data = [
        {"id": 8, "en": "Digital Services", "ga": "Seirbhísí Digiteacha"},
        {"id": 3, "en": "Digital Workforce", "ga": "Fórsa Saothair Digiteach"},
        {"id": 4, "en": "Digital Systems", "ga": "Córais Dhigiteacha"},
        {"id": 5, "en": "Digital Communities", "ga": "Pobail Dhigiteacha"},
    ]

    print("--- STEP 2: SEEDING DATA WITH SERIAL TITLES ---")
    total_actions = 122
    completed_target = 40
    in_progress_target = 40
    action_counter = 1

    # Max objectives total = 29
    objectives_per_theme = [15, 8, 6, 5]
    all_objectives = []
    objective_counter = 1
    max_objectives = 29

    for item, obj_count in zip(themes_data, objectives_per_theme):
        theme = Theme.objects.create(pk=item["id"], title=item["en"], title_ga=item["ga"])

        for i in range(1, obj_count + 1):
            if objective_counter > max_objectives:
                break
            obj = Objective.objects.create(
                title=f"{objective_counter:03d}",
                description=f"<div><p>{mega_text[:150]}...</p></div>",
                theme=theme
            )
            all_objectives.append(obj)
            objective_counter += 1

    for i in range(total_actions):
        obj = all_objectives[i % len(all_objectives)]

        # Format: ACT_ACC_001, ACT_ACC_002, etc.
        serial_title = f"ACT_ACC_{action_counter:03d}"

        # Small Description: Exactly 10 words
        short_desc = "This is a ten word short description for testing purposes."

        if i < completed_target:
            status = ActionStatus.COMPLETED
        elif i < completed_target + in_progress_target:
            status = ActionStatus.IN_PROGRESS
        else:
            status = ActionStatus.NOT_STARTED

        update_text = f"<div><p>{mega_text}</p></div>" if status != ActionStatus.NOT_STARTED else ""

        Action.objects.create(
            title=serial_title,
            small_description=short_desc,
            # Real heavy text for the expansion test
            description=f"<div><p>{mega_text}</p><p>{mega_text}</p></div>",
            update=update_text,
            objective=obj,
            status=status,
            is_approved=True
        )
        action_counter += 1

    print(f"--- SUCCESS: {action_counter - 1} ACTIONS CREATED (ALL NOT_STARTED) ---")

if __name__ == '__main__':
    seed()
