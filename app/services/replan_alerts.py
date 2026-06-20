from datetime import datetime


def should_create_replan_alert(
    old_urgency,
    new_urgency,
    old_severity,
    new_severity,
):
    severity_order = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }

    if new_urgency - old_urgency >= 20:
        return True

    if severity_order.get(new_severity, 0) > severity_order.get(old_severity, 0):
        return True

    return False


def build_alert_reason(
    old_urgency,
    new_urgency,
    old_severity,
    new_severity,
):
    changes = []

    if new_urgency > old_urgency:
        changes.append(f"urgency increased {old_urgency}→{new_urgency}")

    if old_severity != new_severity:
        changes.append(f"severity changed {old_severity}→{new_severity}")

    return ", ".join(changes)


def create_replan_alert(
    spreadsheet,
    student_id,
    severity,
    urgency,
    reason,
):
    worksheet = spreadsheet.worksheet("replan_alerts")

    worksheet.append_row(
        [
            student_id,
            severity,
            urgency,
            reason,
            datetime.now().isoformat(),
            "No",
        ]
    )
