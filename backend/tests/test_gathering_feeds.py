"""Offline parser and HTTP boundary tests. No public endpoint is contacted."""
import hashlib
from datetime import datetime

import httpx
import pytest

from app.gathering import feeds
from app.gathering.catalog import CATALOG
from app.gathering.feeds import FeedError, fetch_feed, parse_date, parse_feed, plain_text, public_url

BASE = "https://www.federalreserve.gov/feeds/press_monetary.xml"


def rss(items):
    return ('<?xml version="1.0"?><rss version="2.0"><channel>' + items + '</channel></rss>').encode()


def item(title="Decision", link="https://www.federalreserve.gov/newsevents/pressreleases/test.htm", extra=""):
    return f"<item><title>{title}</title><link>{link}</link>{extra}</item>"


def test_rss_preserves_publisher_times_and_plain_summary():
    result = parse_feed(rss(item(extra="""<guid isPermaLink="false">release:7</guid>
      <description><![CDATA[<p>Rates <b>unchanged</b>.</p><script>secret()</script><p>Read &amp; compare.</p>]]></description>
      <pubDate>Tue, 27 Oct 2026 12:00:00 -0400</pubDate>""")), base_url=BASE)
    assert result == {"items": [{"external_id": "release:7", "url": "https://www.federalreserve.gov/newsevents/pressreleases/test.htm",
                               "title": "Decision", "summary": "Rates unchanged . Read & compare.",
                               "published_at": "2026-10-27T16:00:00+00:00", "updated_at": None,
                               "published_raw": "Tue, 27 Oct 2026 12:00:00 -0400", "updated_raw": None}],
                      "skipped_items": 0, "truncated": False}


def test_atom_distinguishes_update_and_publication_and_selects_article_link():
    body = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>tag:example.org,2020:7</id>
      <title>A &amp; B</title><link rel="self" href="https://example.org/api/7"/>
      <link rel="alternate" href="/article#section"/>
      <summary type="html">&lt;p&gt;Summary only&lt;/p&gt;</summary>
      <content>Do not import the full article.</content>
      <published>2020-01-02T10:00:00Z</published><updated>2026-10-27T12:00:00+02:00</updated>
      </entry></feed>'''
    row = parse_feed(body, base_url="https://example.org/feed")["items"][0]
    assert row["url"] == "https://example.org/article"
    assert row["summary"] == "Summary only"
    assert row["published_at"] == "2020-01-02T10:00:00+00:00"
    assert row["updated_at"] == "2026-10-27T10:00:00+00:00"


def test_missing_summary_does_not_fall_back_to_full_content():
    body = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Title</title>
      <link href="https://example.org/a"/><content>Full text</content><updated>2026-01-01T00:00:00Z</updated>
      </entry></feed>'''
    row = parse_feed(body, base_url=BASE)["items"][0]
    assert row["summary"] == ""
    assert row["published_at"] is None
    assert row["external_id"] == row["url"]


def test_rss_guid_permalink_fallback_and_latin1_encoding():
    body = '''<?xml version="1.0" encoding="ISO-8859-1"?><rss><channel><item>
      <title>Énergie</title><guid>https://example.org/energy</guid></item></channel></rss>'''.encode("latin-1")
    row = parse_feed(body, base_url=BASE)["items"][0]
    assert row["title"] == "Énergie"
    assert row["url"] == "https://example.org/energy"


@pytest.mark.parametrize("date", [None, "", "not a date", "2020-01-02", "2020-01-02T01:02:03", "Tue, 27 Oct 2026 12:00:00", "Tue, 99 Foo 2026 12:00:00 GMT"])
def test_invalid_or_timezone_missing_dates_are_unknown(date):
    assert parse_date(date) is None


def test_future_publication_claim_is_not_clamped_to_import_time():
    assert parse_date("2099-01-01T01:00:00+01:00") == "2099-01-01T00:00:00+00:00"
    row = parse_feed(rss(item(extra="<pubDate>Wed, 01 Jan 2099 00:00:00 GMT</pubDate>")), base_url=BASE)["items"][0]
    assert row["published_at"].startswith("2099-")
    assert "first_seen_at" not in row and "recorded_at" not in row


@pytest.mark.parametrize("url", ["javascript:alert(1)", "data:text/html,test", "file:///C:/secret", "https://user:pass@example.org/a", "http://127.0.0.1/a", "http://[::1]/a", "http://169.254.169.254/", "http://localhost/a", "http://host.internal/a", "http://192.168.1.1/a", "http://127.1/a", "https://example.org:8443/a", "https://example.org/\nattack"])
def test_unsafe_article_links_rejected(url):
    assert public_url(url) is None


def test_article_url_normalization_preserves_meaningful_query():
    assert public_url("HTTPS://Example.org:443/a?release=7#top") == "https://example.org/a?release=7"
    assert public_url("/article?id=7", "https://example.org/feed") == "https://example.org/article?id=7"


def test_invalid_items_are_counted_and_feed_volume_capped():
    body = rss(item(link="javascript:alert(1)") + item(title="") + "".join(item(title=f"Item {i}") for i in range(110)))
    result = parse_feed(body, base_url=BASE)
    assert len(result["items"]) == 98
    assert result["skipped_items"] == 2
    assert result["truncated"] is True


@pytest.mark.parametrize("body,code", [
    (b"<rss>", "INVALID_FEED_XML"),
    (b"<html><body>Gateway error</body></html>", "UNSUPPORTED_FEED"),
    (b"<rss/>", "INVALID_FEED_XML"),
    (b'<!DOCTYPE rss [<!ENTITY x "expansion">]><rss><channel>&x;</channel></rss>', "UNSAFE_FEED_XML"),
    ('<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE rss SYSTEM "file:///secret"><rss/>'.encode("utf-16"), "UNSAFE_FEED_XML"),
    (b"<rss>" + b"<a>" * 40 + b"</a>" * 40 + b"</rss>", "FEED_XML_LIMIT"),
    (b"x" * (feeds.MAX_BYTES + 1), "FEED_TOO_LARGE"),
], ids=["malformed", "html", "no-channel", "entity", "utf16-dtd", "too-deep", "too-large"])
def test_bad_or_unsafe_feed_fails_closed(body, code):
    with pytest.raises(FeedError) as error:
        parse_feed(body, base_url=BASE)
    assert error.value.code == code
    assert "secret" not in str(error.value)


def test_plaintext_has_bounded_length_and_strips_active_markup():
    assert plain_text('<img src="x" onerror="steal()">safe<script>steal()</script><style>bad</style> text') == "safe text"
    assert plain_text("x" * 100, 8) == "xxxxxxxx"


class Chunks(httpx.SyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks
    def __iter__(self):
        yield from self.chunks


def transport_for(body, status=200, headers=None):
    def handle(request):
        assert str(request.url) == BASE
        assert request.headers["accept-encoding"] == "identity"
        assert "authorization" not in request.headers
        return httpx.Response(status, headers=headers, stream=Chunks([body]))
    return httpx.MockTransport(handle)


def test_fetch_contacts_only_catalog_endpoint_and_retains_digest():
    body = rss(item())
    result = fetch_feed("fed-monetary", transport=transport_for(body))
    assert result["http_status"] == 200
    assert result["content_sha256"] == hashlib.sha256(body).hexdigest()
    assert datetime.fromisoformat(result["fetched_at"]).utcoffset().total_seconds() == 0
    assert len(result["items"]) == 1


def test_unknown_catalog_key_never_calls_transport():
    def no_request(request):
        pytest.fail("Arbitrary URL reached the transport")
    with pytest.raises(FeedError, match="catalog"):
        fetch_feed("http://localhost/secret", transport=httpx.MockTransport(no_request))


@pytest.mark.parametrize("status,headers,code", [
    (302, {"location": "http://localhost/secret"}, "FEED_REDIRECT"),
    (403, {}, "FEED_HTTP_ERROR"),
    (429, {}, "FEED_HTTP_ERROR"),
    (200, {"content-encoding": "gzip"}, "FEED_ENCODING"),
    (200, {"content-length": str(feeds.MAX_BYTES + 1)}, "FEED_TOO_LARGE"),
])
def test_http_failures_redirects_and_compressed_bodies_fail_closed(status, headers, code):
    with pytest.raises(FeedError) as error:
        fetch_feed("fed-monetary", transport=transport_for(b"provider secret debug info", status, headers))
    assert error.value.code == code
    assert "secret" not in str(error.value) and "localhost" not in str(error.value)


def test_streamed_size_limit_without_content_length():
    with pytest.raises(FeedError) as error:
        fetch_feed("fed-monetary", transport=transport_for(b"x" * (feeds.MAX_BYTES + 1)))
    assert error.value.code == "FEED_TOO_LARGE"


@pytest.mark.parametrize("exception,code", [(httpx.ReadTimeout, "FEED_TIMEOUT"), (httpx.ConnectError, "FEED_NETWORK_ERROR")])
def test_transport_exceptions_are_sanitized(exception, code):
    def fail(request):
        raise exception("https://secret:password@provider/error", request=request)
    with pytest.raises(FeedError) as error:
        fetch_feed("fed-monetary", transport=httpx.MockTransport(fail))
    assert error.value.code == code
    assert "password" not in str(error.value)


def test_total_deadline_is_checked_across_read_chunks(monkeypatch):
    ticks = iter([0.0, feeds.TOTAL_SECONDS + .1])
    monkeypatch.setattr(feeds.time, "monotonic", lambda: next(ticks))
    with pytest.raises(FeedError) as error:
        fetch_feed("fed-monetary", transport=transport_for(rss(item())))
    assert error.value.code == "FEED_TIMEOUT"


def test_catalog_is_https_fixed_and_has_official_provenance():
    assert {"nvidia-news", "aws-news", "fed-monetary", "ecb-press", "eu-council", "eia-energy"} <= CATALOG.keys()
    for key, source in CATALOG.items():
        assert source["key"] == key
        assert public_url(source["url"]) == source["url"]
        assert source["url"].startswith("https://")
        assert source["reference_url"].startswith("https://")
