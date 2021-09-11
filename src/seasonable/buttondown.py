import attr

@attr.s(frozen=True, auto_attribs=True)
class Buttondown:
    _token: str
        
    def update_request(self, method, api, **kwargs):
        headers = {'Authorization': f'Token {self._token}'}
        headers.update(kwargs.pop("headers", {}))
        kwargs["headers"] = headers
        url = f"https://api.buttondown.email/{api}"
        return url, kwargs