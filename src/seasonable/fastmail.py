# Inspired by https://jvns.ca/blog/2020/08/18/implementing--focus-and-reply--for-fastmail/
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

def get_inbox_id(client, account_id):
    query=[[
        "Mailbox/get",
        dict(
            accountId=account_id,
            ids=None,
        ),
        0,
    ]]
    mbox = jmap_call(client, query)
    [inbox] = [folder for folder in mbox["methodResponses"][0][1]["list"] if folder["role"]=="inbox"]
    mailbox_id = inbox["id"]
    return mailbox_id

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