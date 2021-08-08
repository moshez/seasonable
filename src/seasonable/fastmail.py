# Inspired by https://jvns.ca/blog/2020/08/18/implementing--focus-and-reply--for-fastmail/
from __future__ import annotations
import attr
import collections

@attr.s(frozen=True, auto_attribs=True)
class Fastmail:

    _username: str
    _token: str
    
    def update_request(self, method, api, **kwargs):
        kwargs["auth"] = (self._username, self._token)
        url = f"https://jmap.fastmail.com/{api}"
        return url, kwargs

def make_jmap_query(method_calls):
    return {
        "using": [ "urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail" ],
        "methodCalls": method_calls,
    }

def jmap_call(client, method_calls):
    return client.post("api", json=make_jmap_query(method_calls))


def get_account_id(client):
    session = client.get(".well-known/jmap")
    account_id = session['primaryAccounts']['urn:ietf:params:jmap:mail']
    return account_id

def get_id_by_role(client, account_id):
    query=[[
        "Mailbox/get",
        dict(
            accountId=account_id,
            ids=None,
        ),
        0,
    ]]
    mbox = jmap_call(client, query)
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
    results = jmap_call(client, get_emails_query)
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
    jmap_call(client, query)
    
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
        account_id = get_account_id(fastmail_client)
        roles = get_id_by_role(fastmail_client, account_id)
        return cls(client=fastmail_client, roles=roles, account_id=account_id)

    def get_inbox(self):
        mailbox_id = self.roles["inbox"]
        threads = get_threads(self.client, self.account_id, mailbox_id)
        emails = [email_from_thread(thread) for thread in threads]
        return emails
    
    def archive(self, email_id):
        move_email(self.client, account_id=self.account_id, email_id=email_id, mailbox_id=self.roles["archive"])