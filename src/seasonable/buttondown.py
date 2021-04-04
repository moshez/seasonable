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

def get_subscribers(client):
    api = "v1/subscribers"
    subscribers = []
    while api is not None:
        res = client.get(api)
        subscribers.extend(res["results"])
        next_text = res.get("next")
        if next_text is None:
            api = None
        else:
            next_link = hyperlink.URL.from_text(res["next"])
            api = "/".join(next_link.path) + "?" + "&".join(map("=".join, next_link.query))
    return subscribers

def save_subscribers(path, subscribers):
    emails = [sub["email"] for sub in subscribers]
    path.write_text(json.dumps(emails))