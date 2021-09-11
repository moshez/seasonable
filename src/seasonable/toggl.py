from __future__ import annotations
import datetime
import attr

from . import client as clientlib

@attr.s(frozen=True, auto_attribs=True)
class Toggl:
    _user: str

    def update_request(self, method, api, **kwargs):
        kwargs["auth"] = (self._token, 'api_token')
        url = f"https://www.toggl.com/{api}"
        headers = dict(user_agent="seasonable/python")
        headers.update(kwargs.pop("headers", {}))
        kwargs["headers"] = headers
        if api.startswith("reports/api/v2/"):
            params = dict(user_agent="seasonable/python")
            params.update(kwargs.pop("params"))
            kwargs["params"] = params
        return url, kwargs
