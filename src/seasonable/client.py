from __future__ import annotations
import attr

@attr.s(frozen=True, auto_attribs=True)
class APIClient:
    _client: Any
    _api_handler: Any

    def request(self, method, api, **kwargs):
        api = api.lstrip("/")
        url, kwargs = self._api_handler.update_request(method, api, **kwargs)
        resp = self._client.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def get(self, api, **params):
        return self.request("GET", api, **params)
    
    def post(self, api, **params):
        return self.request("POST", api, **params)
    
    @classmethod
    def from_class(cls, client, handler_class, path):
        parts = path.read_text().splitlines()
        return cls(client, handler_class(*parts))
    