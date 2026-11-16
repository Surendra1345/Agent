from fastapi.testclient import TestClient

import agent.api as api

client = TestClient(api.app)


def test_rejects_non_pdf():
    assert client.post("/api/chat", files={"file": ("x.txt", b"hi")}).status_code == 400


def test_rejects_bad_magic():
    assert client.post("/api/chat", files={"file": ("x.pdf", b"hello")}).status_code == 400


def test_corrupt_pdf_returns_422_and_is_deleted():
    before = set(api.UPLOAD_DIR.iterdir())
    r = client.post("/api/chat", files={"file": ("../../evil.pdf", b"%PDF-1.4 broken")})
    assert r.status_code == 422
    assert set(api.UPLOAD_DIR.iterdir()) == before  # nothing left behind, no traversal
