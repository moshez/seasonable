from dateutil import parser

def recently_completed_by_label(client, label_name, since):
    all_labels = client.get("rest/v1/labels")
    [label] = [a_label for a_label in all_labels if a_label["name"] == label_name]
    completed = client.post("sync/v8/activity/get", json=dict(event_type="completed", limit=100))
    result = []
    for an_event in completed["events"]:
        when = parser.isoparse(an_event["event_date"])
        if when < since:
            continue        
        task_id = an_event["object_id"]
        try:
            details = client.post("sync/v8/items/get", json=dict(item_id=task_id))["item"]
        except Exception:
            pass
        if label["id"] in details["labels"]:
            result.append((details, an_event))
    return result


def make_task(todoist_client, subject, description):
    todoist_client.post("rest/v1/tasks", json=dict(content=subject, description=description))