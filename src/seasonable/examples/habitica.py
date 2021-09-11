from __future__ import annotations
import attr
import collections
import datetime
import enum
import ipywidgets

from .. import ui

@enum.unique
class Direction(enum.Enum):
    UP = "up"
    DOWN = "down"
    

def get_habits_by_tag(client, tag):
    tasks = client.get("/api/v3/tasks/user")
    tags = client.get("/api/v3/tags")
    [tag_id] = [t["id"] for t in tags["data"] if t["name"] == tag]
    tagged_habits = {
        task["id"]: task["text"]

        for task in tasks["data"]
        if (
            task["type"] == "habit"
            and
            tag_id in task["tags"]
        )
    }
    return tagged_habits

def update_habit(client, habit_id, direction):
    api = f"/api/v3/tasks/{habit_id}/score/{direction.value}"
    res = client.post(api)
    res.raise_for_status()
    value = res.json()
    if not value["success"]:
        raise ValueErrror(res)
    return value


def _make_grid_template(builder, length, children):
    grid_template_rows = " ".join(["auto"] * length)
    grid_template_columns='80% 10% 10%'
    grid_template_areas = "".join([
        f'"label_{i} up_{i} down_{i}"\n'
        for i in range(length)
    ]) + '"output output output"\n'
    builder.add_widgets(
        grid=ipywidgets.GridBox(
            children=children + [builder.ui_output],
            layout=ipywidgets.Layout(
                width='50%',
                grid_template_rows=grid_template_rows,
                grid_template_columns=grid_template_columns,
                grid_template_areas=grid_template_areas,
            ),
        ),
    )

def _make_button(*, idx, output, client, habit_id, direction):
    def clicker(button):
        with output:
            print("hooray")
            res = update_habit(client, habit_id, direction)
            print(direction, res["success"])
    button = ipywidgets.Button(
                description='',
                icon=f'thumbs-{direction.value}',
                layout=ipywidgets.Layout(grid_area=f"{direction.value}_{idx}", width="auto"),
            )
    button.on_click(clicker)
    return button


def label_button_gridbox(client, habits):
    builder = ui.UIBuilder()
    builder.add_widgets(output=ipywidgets.Output())
    def get_children():
        for i, (habit_id, habit_text) in enumerate(habits.items()):
            for direction in Direction:
                yield _make_button(idx=i, output=builder.ui_output, client=client, habit_id=habit_id, direction=direction)
        yield ipywidgets.Label(
            habit_text,
            layout=ipywidgets.Layout(grid_area=f"label_{i}"),
        )
    _make_grid_template(builder, len(habits), children=list(get_children()))
    return builder.ui_grid

def get_clicks_by_date(client, name):
    tasks = client.get("/api/v3/tasks/user")
    [relevant] = [item for item in tasks["data"] if item["text"] == name]
    history = relevant["history"]
    
    clicks = [(datetime.datetime.fromtimestamp(item["date"]/1000), item) for item in history]
    by_date = collections.defaultdict(list)
    for when, item in clicks:
        by_date[when.date()].append(item)
    return by_date