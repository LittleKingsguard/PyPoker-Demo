#!/usr/bin/env python3
"""Serve the PyPoker interactive table.

A single-file, dependency-free HTTP server (the Python standard library only) that
serves ``ui/static`` and a small JSON API around :mod:`table`.  Run it from the
repository root::

    .venv/bin/python ui/serve.py --open

The server binds to localhost by default.  It is a demo tool and has no
authentication: do not expose it to an untrusted network.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import secrets
import sys
import threading
import traceback
import webbrowser
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from table import (  # noqa: E402
    DEFAULT_SHAPE,
    Match,
    Registry,
    UIError,
    parse_seed,
    shape_config,
    shape_label,
)

STATIC = HERE / "static"
COOKIE = "pypoker_sid"
MAX_BODY = 1 << 20


class Client:
    """One browser's match, serialised by its own lock."""

    def __init__(self) -> None:
        self.match: Match | None = None
        self.lock = threading.Lock()


class UIServer(ThreadingHTTPServer):
    daemon_threads = True
    #: The default backlog is 5.  A browser fires several requests when a model is changed, and a
    #: probe policy's first load takes ~2.5 s, so a small backlog drops connections and the page
    #: reports "failed to fetch".  Queue the burst instead.
    request_queue_size = 128
    allow_reuse_address = True

    def __init__(self, address, registry: Registry):
        self.registry = registry
        self.clients: dict[str, Client] = {}
        self.clients_lock = threading.Lock()
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "PyPokerUI/1.0"

    # -- plumbing ----------------------------------------------------------

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(
        self,
        status: int,
        body: bytes,
        content_type: str,
        cookie: str | None = None,
        extra: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(
        self,
        payload: Any,
        status: int = 200,
        cookie: str | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(
            status,
            body,
            "application/json; charset=utf-8",
            cookie=cookie,
        )

    def _error(self, status: int, message: str) -> None:
        self._json({"error": message}, status=status)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise UIError("Bad Content-Length") from None
        if length <= 0:
            return {}
        if length > MAX_BODY:
            raise UIError("Request body is too large")
        raw = self.rfile.read(length)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise UIError("Request body is not JSON") from None
        if not isinstance(value, dict):
            raise UIError("Request body must be a JSON object")
        return value

    # -- sessions ----------------------------------------------------------

    def _sid(self) -> str | None:
        raw = self.headers.get("Cookie", "")
        if not raw:
            return None
        jar = SimpleCookie()
        try:
            jar.load(raw)
        except Exception:
            return None
        morsel = jar.get(COOKIE)
        return morsel.value if morsel is not None else None

    def _client(self, create: bool = False) -> tuple[str | None, Client | None, str | None]:
        """``(sid, client, set_cookie)``; creates a session when asked."""
        sid = self._sid()
        if sid is not None:
            with self.server.clients_lock:
                client = self.server.clients.get(sid)
            if client is not None:
                return sid, client, None
        if not create:
            return sid, None, None
        sid = secrets.token_urlsafe(18)
        client = Client()
        with self.server.clients_lock:
            self.server.clients[sid] = client
        cookie = "%s=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000" % (
            COOKIE,
            sid,
        )
        return sid, client, cookie

    # -- routing -----------------------------------------------------------

    def do_GET(self) -> None:
        path = unquote(urlparse(self.path).path)
        try:
            if path == "/api/opponents":
                self._json(self.server.registry.opponents())
                return
            if path == "/api/health":
                league = self.server.registry.opponents()
                self._json(
                    {
                        "ok": True,
                        "models": len(league["models"]),
                        "baselines": len(league["baselines"]),
                    }
                )
                return
            if path == "/api/state":
                _sid, client, _cookie = self._client(create=False)
                if client is None or client.match is None:
                    self._json({"match": None})
                    return
                with client.lock:
                    self._json(client.match.state())
                return
            self._static(path)
        except UIError as error:
            self._error(400, str(error))
        except Exception as error:  # pragma: no cover - last-resort report
            traceback.print_exc()
            self._error(500, "Unexpected server error: %s" % (error,))

    def do_POST(self) -> None:
        path = unquote(urlparse(self.path).path)
        try:
            body = self._read_json()
            if path == "/api/start":
                self._start(body)
                return
            if path == "/api/action":
                self._action(body)
                return
            if path == "/api/next":
                self._next()
                return
            if path == "/api/reset":
                _sid, client, _cookie = self._client(create=False)
                if client is not None:
                    with client.lock:
                        client.match = None
                self._json({"match": None})
                return
            self._error(404, "No such endpoint: %s" % (path,))
        except UIError as error:
            self._error(400, str(error))
        except Exception as error:  # pragma: no cover - last-resort report
            traceback.print_exc()
            self._error(500, "Unexpected server error: %s" % (error,))

    # -- API ---------------------------------------------------------------

    def _start(self, body: dict[str, Any]) -> None:
        opponent_id = body.get("opponent_id")
        if not isinstance(opponent_id, str) or not opponent_id:
            raise UIError("Choose an opponent first")
        registry = self.server.registry
        opponent = registry.get(opponent_id)

        shape = body.get("shape")
        if opponent.kind == "model":
            shape = opponent.shape
        elif not isinstance(shape, str) or not shape:
            shape = DEFAULT_SHAPE
        if not isinstance(shape, str):
            raise UIError("The table shape must be a name")
        config = shape_config(shape)
        seats = int(config["seats"])

        seat = body.get("seat", 0)
        if isinstance(seat, bool) or not isinstance(seat, int) or seat not in range(seats):
            raise UIError(
                "The seat must be between 0 and %d for a %s table"
                % (seats - 1, shape_label(shape))
            )
        seed = parse_seed(body.get("seed"))
        if seed is None:
            seed = secrets.randbelow(2**31 - 1) + 1

        lineup_mode = body.get("lineup_mode", "same")
        if lineup_mode not in ("same", "mixed") or seats <= 2:
            lineup_mode = "same"

        if lineup_mode == "mixed":
            lineup = registry.mixed_lineup(
                shape,
                seed,
                seats - 1,
                anchor=opponent,
            )
            occupants = [index for index in range(seats) if index != seat]
            members = {index: member for index, member in zip(occupants, lineup)}
        else:
            members = {
                index: opponent for index in range(seats) if index != seat
            }

        _sid, client, cookie = self._client(create=True)
        assert client is not None
        with client.lock:
            client.match = Match(
                registry,
                opponent,
                human_seat=seat,
                seed=seed,
                shape=shape,
                members=members,
                lineup_mode=lineup_mode,
            )
            state = client.match.state()
        self._json(state, cookie=cookie)

    def _action(self, body: dict[str, Any]) -> None:
        action = body.get("action")
        if not isinstance(action, str) or not action:
            raise UIError("The action must be a descriptor")
        _sid, client, _cookie = self._client(create=False)
        if client is None or client.match is None:
            raise UIError("Start a match before acting")
        with client.lock:
            state = client.match.act(action)
        self._json(state)

    def _next(self) -> None:
        _sid, client, _cookie = self._client(create=False)
        if client is None or client.match is None:
            raise UIError("Start a match before dealing a hand")
        with client.lock:
            state = client.match.next_hand()
        self._json(state)

    # -- static files ------------------------------------------------------

    def _static(self, path: str) -> None:
        if path in ("/", "/index.html"):
            target = STATIC / "index.html"
        elif path.startswith("/static/"):
            target = STATIC / path[len("/static/") :]
        elif path == "/favicon.svg":
            target = STATIC / "favicon.svg"
        else:
            self._error(404, "Not found")
            return
        try:
            resolved = target.resolve()
            resolved.relative_to(STATIC.resolve())
        except (ValueError, OSError):
            self._error(404, "Not found")
            return
        if not resolved.is_file():
            self._error(404, "Not found")
            return
        content_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in (
            "application/javascript",
            "application/json",
            "image/svg+xml",
        ):
            content_type += "; charset=utf-8"
        self._send(200, resolved.read_bytes(), content_type)


def make_server(
    registry: Registry,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> UIServer:
    """One bound server, for ``main`` and for the tests."""
    return UIServer((host, port), registry)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Play the PyPoker league in your browser."
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="port (default: 8000)")
    parser.add_argument(
        "--checkpoint-root",
        default=None,
        help="directory of shipped checkpoints (default: ./checkpoints)",
    )
    parser.add_argument(
        "--probe-root",
        default=None,
        help="directory of research checkpoints (default: ./.probe)",
    )
    parser.add_argument("--open", action="store_true", help="open the browser after starting")
    args = parser.parse_args(argv)

    registry = Registry(args.checkpoint_root, args.probe_root)
    # Warm the saved probe heads: their first load pulls torch into the process, and paying that
    # inside a request makes the first model change feel broken (and fills the accept queue).
    for member in registry.models():
        if getattr(member, "kind", None) == "probe-policy" and member.meta.get("available"):
            try:
                registry.policy_for(member, 0, member.shape)
            except Exception as error:  # a warm-up must never stop the server
                print("warm-up skipped %s: %s" % (member.name, error))
    league = registry.opponents()
    try:
        server = make_server(registry, args.host, args.port)
    except OSError as error:
        print("Could not bind %s:%d: %s" % (args.host, args.port, error), file=sys.stderr)
        return 1
    host, port = server.server_address[:2]
    shown = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    url = "http://%s:%d/" % (shown, port)
    print("PyPoker table: %s" % (url,))
    playable = sum(1 for model in league["models"] if model["available"])
    print(
        "League: %d model checkpoint(s) (%d playable), %d deterministic policies"
        % (len(league["models"]), playable, len(league["baselines"]))
    )
    sources: dict[str, int] = {}
    for model in league["models"]:
        sources[model.get("source_label", "Checkpoint")] = (
            sources.get(model.get("source_label", "Checkpoint"), 0) + 1
        )
    print(
        "Sources: %s · torch %s"
        % (
            ", ".join("%s %d" % (name, count) for name, count in sorted(sources.items())),
            "available" if league.get("torch_available") else "not installed",
        )
    )
    print("Press Ctrl-C to stop.")
    if args.open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
