from __future__ import annotations
import attr
import collections
import datetime
import enum
import ipywidgets

@attr.s(frozen=True, auto_attribs=True)
class Habitica:
    _user: str
    _key: str

    def update_request(self, method, api, **kwargs):
        kwargs["auth"] = (self._user, self._key)
        url = f"https://habitica.com/{api}"
        headers ={
            "x-api-user": self._user,
            "x-api-key": self._key,
        }
        headers.update(kwargs.pop("headers", {}))
        kwargs["headers"] = headers
        return url, kwargs
