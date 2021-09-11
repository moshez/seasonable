# Inspired by https://jvns.ca/blog/2020/08/18/implementing--focus-and-reply--for-fastmail/
from __future__ import annotations
import attr
import collections
from seasonable import ui, todoist
import ipywidgets

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
