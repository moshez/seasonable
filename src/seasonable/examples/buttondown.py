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