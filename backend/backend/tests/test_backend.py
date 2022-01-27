import json

from backend.url_shortener import __version__, app
import datetime

# from dateutil.parser import parse


def test_version():
    assert __version__ == "0.1.1"


# print(f'testing directory: {TEST_DIR}')

# 0. bring up
def test_dummy_to_bring_up_server():
    response = app.test_client().post("/init")

    assert response.status_code == 404


# 1. happy path
def test_post_shorten():
    response = app.test_client().post(
        "/shorten",
        data=json.dumps({"url": "https://example.com", "shortcode": "asd148"}),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))

    assert response.status_code == 201
    assert data["shortcode"] == "asd148"


def test_get_shortcode():
    response = app.test_client().get("/asd148")

    assert response.status_code == 302
    assert response.headers["Location"] == "https://example.com"


def test_get_shortcode_stats():
    response = app.test_client().get("/asd148/stats")

    data = json.loads(response.get_data(as_text=True))

    assert response.status_code == 200
    # assert data["created"].parse == datetime.datetime.now().isoformat()
    # assert data["lastRedirect"].parse == ...
    assert data["redirectCount"] == 1


# 2. errors
def test_post_shorten_malformed_url():
    response = app.test_client().post(
        "/shorten",
        data=json.dumps({"url": "htt576ps://example.com", "shortcode": "asdea4"}),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))

    assert response.status_code == 400
    assert data["error_message"] == "Invalid url"


def test_post_shorten_invalid_shortcode():
    response = app.test_client().post(
        "/shorten",
        data=json.dumps({"url": "https://example.com", "shortcode": "a"}),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))

    assert response.status_code == 412
    assert data["error_message"] == "The provided shortcode is invalid"
