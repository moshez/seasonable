import attr

from dateutil import parser

@attr.s(frozen=True, auto_attribs=True)
class Todoist:

    _token: str
    
    def update_request(self, method, api, **kwargs):
        headers=dict(Authorization=f"Bearer {self._token}")
        headers.update(kwargs.pop("headers", {}))
        kwargs["headers"] = headers
        url = f"https://api.todoist.com/{api}"
        return url, kwargs
