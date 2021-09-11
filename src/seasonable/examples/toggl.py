from __future__ import annotations
import datetime
import attr

def add_entry(client, start: datetime.datetime, duration: datetime.timedelta, what: str) -> Any:
    time_entry=dict(
        created_with="seasonable/python",
        description=what, 
        start=start.isoformat(), 
        duration=duration.total_seconds(),
    )
    return client.post("/api/v8/time_entries", json=dict(time_entry=time_entry))


def get_entries(client, since):
    iso_since = since.isoformat()
    [main_workspace] = client.get("api/v8/workspaces)
    main_workspace_id = main_workspace["id"]
    all_data = []
    def get_page(idx):
        results = client.get(
            "reports/api/v2/details",
            params=dict(workspace_id=main_workspace_id, page=idx),
        )
        total_count = results["total_count"]
        per_page = results["per_page"]
        returned = len(results["data"])
        pages = math.ceil(total_count/per_page)
        all_data.extend(results["data"])
        return pages
    pages = get_page(1)
    for i in range(2, pages + 1):
        get_page(i)
    return all_data
