"""Bounded RSS/Atom reader with no credentials, article fetches or redirects."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html.parser import HTMLParser
import ipaddress
import re
import time
from urllib.parse import urljoin, urlsplit, urlunsplit
from xml.etree import ElementTree
from xml.parsers import expat

import httpx

from app.gathering.catalog import CATALOG

MAX_BYTES = 2 * 1024 * 1024
MAX_ITEMS = 100
MAX_DEPTH = 32
MAX_NODES = 12000
TOTAL_SECONDS = 8
ATOM = "http://www.w3.org/2005/Atom"
DC = "http://purl.org/dc/elements/1.1/"


class FeedError(Exception):
    """Only these stable messages may be displayed or persisted as feed errors."""
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


class _PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.suppressed = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.suppressed += 1
        if not self.suppressed:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.suppressed:
            self.suppressed -= 1
        if not self.suppressed:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.suppressed:
            self.parts.append(data)


def plain_text(value, limit=20000):
    parser = _PlainText()
    parser.feed(value or "")
    parser.close()
    # No markup is returned; callers must still render this as text, not HTML.
    value = " ".join("".join(parser.parts).split())
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)[:limit]


def public_url(value, base_url=None):
    """Normalize a safe public article link; this function never fetches it."""
    if not value or len(value) > 2048 or "\\" in value or re.search(r"[\x00-\x20\x7f]", value):
        return None
    try:
        parsed = urlsplit(urljoin(base_url, value) if base_url else value)
        hostname = (parsed.hostname or "").lower().rstrip(".").encode("idna").decode("ascii")
        if parsed.scheme.lower() not in {"http", "https"} or not hostname or parsed.username is not None or parsed.password is not None:
            return None
        if hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal")):
            return None
        try:
            if not ipaddress.ip_address(hostname).is_global:
                return None
        except ValueError:
            if "." not in hostname or hostname.rsplit(".", 1)[-1].isdigit() or not re.fullmatch(r"[a-z0-9.-]+", hostname):
                return None
        port = parsed.port
        if port and port not in {80, 443}:
            return None
        host = f"[{hostname}]" if ":" in hostname else hostname
        if port and not (parsed.scheme.lower() == "https" and port == 443 or parsed.scheme.lower() == "http" and port == 80):
            host += f":{port}"
        return urlunsplit((parsed.scheme.lower(), host, parsed.path or "/", parsed.query, ""))
    except (UnicodeError, ValueError):
        return None


def parse_date(value):
    """Publisher claims stay separate from actual retrieval time, even if future."""
    if not value:
        return None
    value = value.strip()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (ValueError, TypeError, OverflowError):
            return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    try:
        return parsed.astimezone(timezone.utc).isoformat()
    except (ValueError, OverflowError):
        return None


def _xml_tree(body):
    if len(body) > MAX_BYTES:
        raise FeedError("FEED_TOO_LARGE", "The feed exceeded the 2 MiB download limit.")
    # Expat checks declarations across encodings (including UTF-16); a byte regex
    # alone would allow an encoded DTD/entity declaration to bypass the guard.
    checker = expat.ParserCreate()
    depth = nodes = 0

    def forbidden(*args):
        raise FeedError("UNSAFE_FEED_XML", "The feed contains unsupported XML declarations.")

    def start(name, attributes):
        nonlocal depth, nodes
        depth += 1
        nodes += 1
        if depth > MAX_DEPTH or nodes > MAX_NODES:
            raise FeedError("FEED_XML_LIMIT", "The feed exceeds the XML structure limit.")

    def end(name):
        nonlocal depth
        depth -= 1

    checker.StartDoctypeDeclHandler = forbidden
    checker.EntityDeclHandler = forbidden
    checker.ExternalEntityRefHandler = forbidden
    checker.StartElementHandler = start
    checker.EndElementHandler = end
    try:
        checker.Parse(body, True)
        return ElementTree.fromstring(body)
    except (expat.ExpatError, ElementTree.ParseError, ValueError):
        raise FeedError("INVALID_FEED_XML", "The source did not return valid RSS or Atom XML.") from None


def _text(element, path):
    node = element.find(path)
    return "".join(node.itertext()).strip() if node is not None else ""


def parse_feed(body, *, base_url):
    root = _xml_tree(body)
    if root.tag == "rss":
        channel = root.find("channel")
        if channel is None:
            raise FeedError("INVALID_FEED_XML", "The RSS feed has no channel.")
        entries = channel.findall("item")
        is_atom = False
    elif root.tag == f"{{{ATOM}}}feed":
        entries = root.findall(f"{{{ATOM}}}entry")
        is_atom = True
    else:
        raise FeedError("UNSUPPORTED_FEED", "The source did not return a supported RSS or Atom feed.")
    items, skipped = [], 0
    for entry in entries[:MAX_ITEMS]:
        if is_atom:
            title = _text(entry, f"{{{ATOM}}}title")
            links = [link for link in entry.findall(f"{{{ATOM}}}link") if link.get("rel", "alternate") == "alternate"]
            raw_url = links[0].get("href", "") if links else ""
            external_id = _text(entry, f"{{{ATOM}}}id")
            summary = _text(entry, f"{{{ATOM}}}summary")
            published = _text(entry, f"{{{ATOM}}}published")
            updated = _text(entry, f"{{{ATOM}}}updated")
        else:
            title, raw_url, external_id = (_text(entry, name) for name in ("title", "link", "guid"))
            summary = _text(entry, "description")
            published = _text(entry, "pubDate") or _text(entry, f"{{{DC}}}date")
            updated = _text(entry, f"{{{ATOM}}}updated")
            if not raw_url and entry.find("guid") is not None and entry.find("guid").get("isPermaLink", "true").lower() != "false":
                raw_url = external_id
        # Do not silently import full content: only publisher-supplied summaries.
        url = public_url(raw_url, base_url)
        title = plain_text(title, 500)
        if not title or not url:
            skipped += 1
            continue
        items.append({"external_id": plain_text(external_id, 1000) or url, "url": url,
                      "title": title, "summary": plain_text(summary),
                      "published_at": parse_date(published), "updated_at": parse_date(updated),
                      "published_raw": published[:200] or None, "updated_raw": updated[:200] or None})
    return {"items": items, "skipped_items": skipped, "truncated": len(entries) > MAX_ITEMS}


def fetch_feed(catalog_key, *, transport=None):
    """Fetch exactly one catalog endpoint. Injection exists for offline tests only."""
    source = CATALOG.get(catalog_key)
    if source is None:
        raise FeedError("UNKNOWN_FEED", "Select a supported public feed from the catalog.")
    deadline = time.monotonic() + TOTAL_SECONDS
    headers = {"User-Agent": "AiTraderLocalResearch/0.1 (RSS reader)",
               "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
               "Accept-Encoding": "identity"}
    try:
        with httpx.Client(timeout=httpx.Timeout(connect=3, read=2, write=2, pool=2),
                          follow_redirects=False, trust_env=False, transport=transport) as client:
            with client.stream("GET", source["url"], headers=headers) as response:
                if 300 <= response.status_code < 400:
                    raise FeedError("FEED_REDIRECT", "The source moved. Its catalog address needs review before collection can continue.")
                if response.status_code != 200:
                    raise FeedError("FEED_HTTP_ERROR", f"The public feed returned HTTP {response.status_code}.")
                if response.headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
                    raise FeedError("FEED_ENCODING", "The source ignored the uncompressed download request.")
                length = response.headers.get("content-length", "")
                if length.isdigit() and int(length) > MAX_BYTES:
                    raise FeedError("FEED_TOO_LARGE", "The feed exceeded the 2 MiB download limit.")
                chunks, size = [], 0
                for chunk in response.iter_raw():
                    if time.monotonic() > deadline:
                        raise FeedError("FEED_TIMEOUT", "The public feed did not complete within the collection time limit.")
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise FeedError("FEED_TOO_LARGE", "The feed exceeded the 2 MiB download limit.")
                    chunks.append(chunk)
                body = b"".join(chunks)
        if time.monotonic() > deadline:
            raise FeedError("FEED_TIMEOUT", "The public feed did not complete within the collection time limit.")
    except httpx.TimeoutException:
        raise FeedError("FEED_TIMEOUT", "The public feed did not complete within the collection time limit.") from None
    except httpx.HTTPError:
        raise FeedError("FEED_NETWORK_ERROR", "The public feed could not be reached. No substitute data was generated.") from None
    return {**parse_feed(body, base_url=source["url"]), "fetched_at": datetime.now(timezone.utc).isoformat(),
            "http_status": 200, "content_sha256": hashlib.sha256(body).hexdigest()}
