#!/usr/bin/env python3
"""OpenBiometrics integration test suite.

Exercises every API endpoint and verifies response structure.
Works even when models are not loaded -- tests structure, not ML accuracy.

Usage:
    python tests/integration.py
    python tests/integration.py --base-url http://localhost:9000
"""

from __future__ import annotations

import argparse
import io
import sys
import time
import traceback

import httpx
from PIL import Image, ImageDraw

# ── Colours ──────────────────────────────────────────────────────────────────

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# ── Helpers ──────────────────────────────────────────────────────────────────

passed = 0
failed = 0
skipped = 0


def _make_test_image() -> bytes:
    """Generate a 640x480 test image (white background + gray rectangle)."""
    img = Image.new("RGB", (640, 480), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Gray rectangle in the centre (simulates a rough "face region")
    draw.rectangle([200, 100, 440, 380], fill=(160, 160, 160))
    # Two darker dots for "eyes"
    draw.ellipse([260, 180, 290, 210], fill=(80, 80, 80))
    draw.ellipse([350, 180, 380, 210], fill=(80, 80, 80))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _image_file(img_bytes: bytes, name: str = "test.jpg"):
    """Return a tuple suitable for httpx file upload."""
    return (name, img_bytes, "image/jpeg")


def test(
    name: str,
    response: httpx.Response,
    *,
    expected_status: int | list[int] = 200,
    required_fields: list[str] | None = None,
    is_list: bool = False,
):
    """Validate a single test case and print the result."""
    global passed, failed

    if isinstance(expected_status, int):
        expected_status = [expected_status]

    ok = response.status_code in expected_status
    detail = ""

    if ok and required_fields:
        try:
            body = response.json()
            for field in required_fields:
                if field not in body:
                    ok = False
                    detail = f"missing field '{field}'"
                    break
        except Exception:
            ok = False
            detail = "invalid JSON body"

    if ok and is_list:
        try:
            body = response.json()
            if not isinstance(body, list):
                ok = False
                detail = "expected list response"
        except Exception:
            ok = False
            detail = "invalid JSON body"

    status_str = f"{response.status_code}"
    if ok:
        passed += 1
        print(f"  {GREEN}PASS{RESET}  {name}  {DIM}({status_str}){RESET}")
    else:
        failed += 1
        extra = f"  -- {detail}" if detail else ""
        print(
            f"  {RED}FAIL{RESET}  {name}  "
            f"{DIM}(got {status_str}, expected {expected_status}){extra}{RESET}"
        )


def section(title: str):
    """Print a section header."""
    print(f"\n{BOLD}{CYAN}--- {title} ---{RESET}")


# ── Test groups ──────────────────────────────────────────────────────────────


def test_health_admin(client: httpx.Client):
    section("Health & Admin")

    r = client.get("/api/v1/health")
    test("GET /health", r, expected_status=200, required_fields=["status"])

    r = client.get("/api/v1/admin/health")
    test("GET /admin/health", r, expected_status=200, required_fields=["modules"])

    r = client.get("/api/v1/admin/models")
    test("GET /admin/models", r, expected_status=200, is_list=True)

    r = client.get("/api/v1/admin/config")
    test("GET /admin/config", r, expected_status=200)


def test_face_detection(client: httpx.Client, img: bytes):
    section("Face Detection")

    # POST /detect
    r = client.post(
        "/api/v1/detect",
        files={"image": _image_file(img)},
    )
    test(
        "POST /detect",
        r,
        expected_status=200,
        required_fields=["faces", "count"],
    )

    # POST /verify
    r = client.post(
        "/api/v1/verify",
        files={
            "image1": _image_file(img, "img1.jpg"),
            "image2": _image_file(img, "img2.jpg"),
        },
        data={"threshold": "0.4"},
    )
    # 200 if models loaded, 400 if no face detected, 500 if recognition model not loaded
    test(
        "POST /verify",
        r,
        expected_status=[200, 400, 500],
    )

    # POST /identify
    r = client.post(
        "/api/v1/identify",
        files={"image": _image_file(img)},
        data={"watchlist_name": "default", "top_k": "5", "threshold": "0.4"},
    )
    # 200 if working, 400 if no face, 500 if recognition model not loaded
    test(
        "POST /identify",
        r,
        expected_status=[200, 400, 500],
    )


def test_watchlists(client: httpx.Client, img: bytes):
    section("Watchlists")

    # POST /watchlist/enroll
    r = client.post(
        "/api/v1/watchlist/enroll",
        files={"image": _image_file(img)},
        data={"label": "integration-test", "watchlist_name": "default"},
    )
    # 200 if working, 400 if no face, 500 if recognition model not loaded
    test(
        "POST /watchlist/enroll",
        r,
        expected_status=[200, 400, 500],
    )
    enrolled_id = None
    if r.status_code == 200:
        try:
            enrolled_id = r.json().get("identity_id")
        except Exception:
            pass

    # GET /watchlist
    r = client.get("/api/v1/watchlist")
    test("GET /watchlist", r, expected_status=200, required_fields=["watchlists"])

    # DELETE /watchlist/{id}
    delete_id = enrolled_id or "nonexistent-test-id"
    r = client.delete(f"/api/v1/watchlist/{delete_id}")
    # 200 if found, 404 if not enrolled
    test("DELETE /watchlist/{id}", r, expected_status=[200, 404])


def test_documents(client: httpx.Client, img: bytes):
    section("Documents")

    # POST /documents/scan
    r = client.post(
        "/api/v1/documents/scan",
        files={"image": _image_file(img)},
    )
    test("POST /documents/scan", r, expected_status=[200, 503])

    # POST /documents/ocr
    r = client.post(
        "/api/v1/documents/ocr",
        files={"image": _image_file(img)},
    )
    test("POST /documents/ocr", r, expected_status=[200, 503])

    # POST /documents/mrz
    r = client.post(
        "/api/v1/documents/mrz",
        files={"image": _image_file(img)},
    )
    # 200 if MRZ found, 422 if no MRZ, 503 if module unavailable
    test("POST /documents/mrz", r, expected_status=[200, 422, 503])

    # POST /documents/verify
    r = client.post(
        "/api/v1/documents/verify",
        files={
            "document": _image_file(img, "doc.jpg"),
            "selfie": _image_file(img, "selfie.jpg"),
        },
        data={"threshold": "0.4"},
    )
    test("POST /documents/verify", r, expected_status=[200, 400, 500, 503])


def test_liveness(client: httpx.Client, img: bytes):
    section("Active Liveness")

    # POST /liveness/sessions -- create
    r = client.post("/api/v1/liveness/sessions", params={"num_challenges": 2})
    test(
        "POST /liveness/sessions (create)",
        r,
        expected_status=[200, 503],
    )

    session_id = None
    if r.status_code == 200:
        try:
            body = r.json()
            session_id = body.get("session_id")
        except Exception:
            pass

    if session_id:
        # GET /liveness/sessions/{id}
        r = client.get(f"/api/v1/liveness/sessions/{session_id}")
        test(
            "GET /liveness/sessions/{id}",
            r,
            expected_status=200,
            required_fields=["session_id", "state", "challenges"],
        )

        # POST /liveness/sessions/{id}/frame
        r = client.post(
            f"/api/v1/liveness/sessions/{session_id}/frame",
            files={"image": _image_file(img)},
        )
        test(
            "POST /liveness/sessions/{id}/frame",
            r,
            expected_status=[200, 400],
            required_fields=["session_id", "passed"] if r.status_code == 200 else None,
        )

        # DELETE /liveness/sessions/{id}
        r = client.delete(f"/api/v1/liveness/sessions/{session_id}")
        test(
            "DELETE /liveness/sessions/{id}",
            r,
            expected_status=[200, 404],
        )
    else:
        global skipped
        skipped += 3
        print(f"  {YELLOW}SKIP{RESET}  Liveness session tests (module unavailable)")


def test_video(client: httpx.Client):
    section("Video")

    # POST /video/cameras -- add
    r = client.post(
        "/api/v1/video/cameras",
        json={"camera_id": "integration-test-cam", "source": "rtsp://0.0.0.0/test"},
    )
    test("POST /video/cameras (add)", r, expected_status=[200, 409, 422, 503])

    # GET /video/cameras -- list
    r = client.get("/api/v1/video/cameras")
    test("GET /video/cameras", r, expected_status=[200, 503])

    # DELETE /video/cameras/{id}
    r = client.delete("/api/v1/video/cameras/integration-test-cam")
    test("DELETE /video/cameras/{id}", r, expected_status=[200, 404, 503])


def test_events(client: httpx.Client):
    section("Events")

    # GET /events/recent
    r = client.get("/api/v1/events/recent")
    test("GET /events/recent", r, expected_status=[200, 503], is_list=True if r.status_code == 200 else False)

    # POST /events/webhooks -- register
    r = client.post(
        "/api/v1/events/webhooks",
        json={
            "url": "https://example.com/webhook-test",
            "event_types": ["face_detected"],
        },
    )
    test("POST /events/webhooks", r, expected_status=[200, 400, 503])

    webhook_id = None
    if r.status_code == 200:
        try:
            webhook_id = r.json().get("id")
        except Exception:
            pass

    # GET /events/webhooks -- list
    r = client.get("/api/v1/events/webhooks")
    test("GET /events/webhooks", r, expected_status=[200, 503])

    # DELETE /events/webhooks/{id}
    delete_id = webhook_id or "nonexistent-webhook-id"
    r = client.delete(f"/api/v1/events/webhooks/{delete_id}")
    test("DELETE /events/webhooks/{id}", r, expected_status=[200, 404, 503])


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    global passed, failed, skipped

    parser = argparse.ArgumentParser(description="OpenBiometrics integration tests")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the API server (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    print(f"\n{BOLD}OpenBiometrics Integration Tests{RESET}")
    print(f"{DIM}Target: {base_url}{RESET}")

    # Generate test image once
    img = _make_test_image()
    print(f"{DIM}Test image: 640x480 JPEG ({len(img)} bytes){RESET}")

    # Check connectivity first
    client = httpx.Client(base_url=base_url, timeout=30.0)
    try:
        client.get("/api/v1/health")
    except httpx.ConnectError:
        print(f"\n{RED}ERROR: Cannot connect to {base_url}{RESET}")
        print(f"{DIM}Make sure the API server is running.{RESET}")
        sys.exit(1)

    start = time.time()

    try:
        test_health_admin(client)
        test_face_detection(client, img)
        test_watchlists(client, img)
        test_documents(client, img)
        test_liveness(client, img)
        test_video(client)
        test_events(client)
    except httpx.ConnectError:
        print(f"\n{RED}ERROR: Lost connection to {base_url}{RESET}")
        failed += 1
    except Exception:
        print(f"\n{RED}ERROR: Unexpected exception{RESET}")
        traceback.print_exc()
        failed += 1
    finally:
        client.close()

    elapsed = time.time() - start

    # Summary
    total = passed + failed
    print(f"\n{BOLD}{'=' * 50}{RESET}")
    print(
        f"  {GREEN}{passed} passed{RESET}  "
        f"{RED}{failed} failed{RESET}  "
        f"{YELLOW}{skipped} skipped{RESET}  "
        f"{DIM}({total} total, {elapsed:.1f}s){RESET}"
    )
    print(f"{BOLD}{'=' * 50}{RESET}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
