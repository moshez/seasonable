# Inspired by https://jvns.ca/blog/2020/08/18/implementing--focus-and-reply--for-fastmail/
from __future__ import annotations

from .. import fastmail, ui, todoist
import attr
import collections
import ipywidgets

def get_id_by_role(client, account_id):
    query=[[
        "Mailbox/get",
        dict(
            accountId=account_id,
            ids=None,
        ),
        0,
    ]]
    mbox = fastmail.jmap_call(client, query)
    roles = {folder["role"]: folder["id"] for folder in mbox["methodResponses"][0][1]["list"] if folder["role"] is not None}
    return roles

def get_threads(client, account_id, mailbox_id):
    get_emails_query = [
    [ "Email/query", {
        "accountId": account_id,
        "filter": { "inMailbox": mailbox_id },
        "sort": [{ "property": "receivedAt", "isAscending": False }],
        "collapseThreads": True,
        "position": 0,
        "limit": 20,
        "calculateTotal": True
    }, "t0" ],
    [ "Email/get", {
            "accountId": account_id,
            "#ids": {
                "resultOf": "t0",
                "name": "Email/query",
                "path": "/ids"
            },
            "properties": [ "threadId" ]
        }, "t1" ],
    [ "Thread/get", {
            "accountId": account_id,
            "#ids": {
                "resultOf": "t1",
                "name": "Email/get",
                "path": "/list/*/threadId"
            }
        }, "t2" ],
    [ "Email/get", {
            "accountId": account_id,
            "fetchTextBodyValues": True,
            "#ids": {
                "resultOf": "t2",
                "name": "Thread/get",
                "path": "/list/*/emailIds"
            },
            "properties": [ "from", "receivedAt", "subject", "bodyValues", "threadId", "mailboxIds"]
    }, "t3" ]
    ]
    results = fastmail.jmap_call(client, get_emails_query)
    name, contents, identifier = results["methodResponses"][-1]
    email_list = contents["list"]
    by_thread = collections.defaultdict(list)
    for email in email_list:
        by_thread[email["threadId"]].append(email)
    return list(by_thread.values())

def move_email(client, *, account_id, email_id, mailbox_id):
    query=[
        [
            "Email/set",
            dict(
                accountId=account_id,
                update={
                    email_id: dict(
                        mailboxIds={mailbox_id: True}
                ),
            }
        ),
        0,
    ]
    ]
    fastmail.jmap_call(client, query)
    
@attr.frozen
class Email:
    id: str
    sender: str
    subject: str

def email_from_thread(thread):
    last_email = thread[-1]
    sender_details = last_email["from"][0]
    name = sender_details.get("name", "")
    email = sender_details["email"]
    sender = f"{name} <{email}>"
    subject = last_email["subject"]
    id = last_email["id"]
    return Email(id=id, sender=sender, subject=subject)


@attr.frozen
class Account:
    account_id: str
    roles: Dict[str, str]
    client: Any
        
    @classmethod
    def from_client(cls, fastmail_client):
        account_id = fastmail.get_account_id(fastmail_client)
        roles = get_id_by_role(fastmail_client, account_id)
        return cls(client=fastmail_client, roles=roles, account_id=account_id)

    def get_inbox(self):
        mailbox_id = self.roles["inbox"]
        threads = get_threads(self.client, self.account_id, mailbox_id)
        emails = [email_from_thread(thread) for thread in threads]
        return emails
    
    def archive(self, email_id):
        move_email(self.client, account_id=self.account_id, email_id=email_id, mailbox_id=self.roles["archive"])
        
        
def _convert_to_task(email, *, todoist_client, account):
    subject = email.subject
    description="From " + email.sender
    email_id = email.id
    print(f"Archiving:\n{subject=}\n{description=}\n{email_id=}")
    todoist.make_task(todoist_client, subject=subject, description=description)
    account.archive(email_id)
        
def _make_grid_template(builder, length, children):
    grid_template_rows = " ".join(["auto"] * length)
    grid_template_columns='80% 20%'
    grid_template_areas = "".join([
        f'"label_{i} convert_{i}"\n'
        for i in range(length)
    ]) + '"output output"\n'
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
    
def _make_button(*, idx, email, todoist_client, account, output):
    def clicker(button):
        with output:
            _convert_to_task(email, todoist_client=todoist_client, account=account)
    button = ipywidgets.Button(
                description='Convert',
                layout=ipywidgets.Layout(grid_area=f"convert_{idx}", width="auto"),
            )
    button.on_click(clicker)
    return button

def label_button_gridbox(emails, todoist_client, account):
    builder = ui.UIBuilder()
    builder.add_widgets(output=ipywidgets.Output())
    def get_children():
        for i, email in enumerate(emails):
            yield _make_button(idx=i, email=email, todoist_client=todoist_client, account=account, output=builder.ui_output)
            yield ipywidgets.Label(
                f"{email.subject[:10]} (from {email.sender})",
                layout=ipywidgets.Layout(grid_area=f"label_{i}"),
            )
    _make_grid_template(builder, len(emails), children=list(get_children()))
    return builder.ui_grid