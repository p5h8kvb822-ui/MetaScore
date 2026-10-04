"""Publication sur Instagram : un carrousel (2 images) par match.
Variables d'environnement : IG_ACCESS_TOKEN, IMAGE_BASE_URL ; optionnelles : IG_USER_ID (défaut « me »),
IG_GRAPH_URL (défaut graph.instagram.com = « API Instagram avec connexion Instagram »).
Si tu utilises la connexion Facebook : IG_GRAPH_URL=https://graph.facebook.com/v23.0 et IG_USER_ID = identifiant du compte."""
import os, sys, json, time, pathlib
import requests

GRAPH = os.getenv("IG_GRAPH_URL", "https://graph.instagram.com/v23.0")


def _call(method, path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    kw = {"data": params} if method == "POST" else {"params": params}
    r = requests.request(method, f"{GRAPH}/{path}", timeout=60, **kw)
    if not r.ok:
        raise RuntimeError(f"Instagram API {r.status_code} : {r.text}")
    return r.json()


def _wait_ready(container_id, tries=30):
    for _ in range(tries):
        st = _call("GET", container_id, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Conteneur {container_id} en échec : {st}")
        time.sleep(3)
    raise RuntimeError(f"Conteneur {container_id} pas prêt à temps")


def publish(manifest_path):
    mf = json.loads(pathlib.Path(manifest_path).read_text(encoding="utf-8"))
    ig = os.getenv("IG_USER_ID", "me")
    base = os.environ["IMAGE_BASE_URL"].rstrip("/")
    errors = 0
    for i, p in enumerate(mf["posts"], 1):
        try:
            urls = [f"{base}/{name}" for name in p["images"]]
            if len(urls) == 1:
                cid = _call("POST", f"{ig}/media", image_url=urls[0], caption=p["caption"])["id"]
            else:  # carrousel : 2 swipes (match + meilleur joueur)
                kids = []
                for u in urls:
                    kid = _call("POST", f"{ig}/media", image_url=u, is_carousel_item="true")["id"]
                    _wait_ready(kid)
                    kids.append(kid)
                cid = _call("POST", f"{ig}/media", media_type="CAROUSEL", children=",".join(kids), caption=p["caption"])["id"]
            _wait_ready(cid)
            pub = _call("POST", f"{ig}/media_publish", creation_id=cid)
            print(f"[{i}/{len(mf['posts'])}] publié, id = {pub.get('id')}")
        except Exception as e:  # on continue avec les autres matchs
            errors += 1
            print(f"[{i}/{len(mf['posts'])}] ÉCHEC : {e}")
        time.sleep(mf.get("pause", 20))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    publish(sys.argv[1])
