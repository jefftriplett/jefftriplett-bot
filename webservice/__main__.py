import aiohttp
import os
import sys

from aiohttp import web
from gidgethub import aiohttp as gh_aiohttp
from gidgethub import routing, sansio


routes = web.RouteTableDef()

router = routing.Router()


@router.register("issues", action="opened")
async def issue_opened_event(event, gh, *args, **kwargs):
    """
    Whenever an issue is opened, greet the author and say thanks.
    """
    url = event.data["issue"]["comments_url"]
    author = event.data["issue"]["user"]["login"]

    message = f"Thanks for the report @{author}! I will look into it ASAP! (I'm a bot)."
    await gh.post(url, data={"body": message})


@routes.post("/")
async def main(request):
    body = await request.read()

    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")

    event = sansio.Event.from_http(request.headers, body, secret=secret)

    print("GH delivery ID", event.delivery_id, file=sys.stderr)

    if event.event == "ping":
        return web.Response(status=200)

    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(
            session, os.getenv("GH_USER"), oauth_token=oauth_token
        )
        await router.dispatch(event, gh)

        try:
            print(
                f"""\
GH requests remaining: {gh.rate_limit.remaining}/{gh.rate_limit.limit}, \
reset time: {gh.rate_limit.reset_datetime:%b-%d-%Y %H:%M:%S %Z}, \
oauth token length {len(oauth_token)}, \
last 4 digits {oauth_token[-4:]}, \
GH delivery ID {event.delivery_id} \
"""
            )
        except AttributeError:
            pass

    return web.Response(status=200)


if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)
