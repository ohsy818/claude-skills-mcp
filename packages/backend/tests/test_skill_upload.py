import asyncio
import json
from io import BytesIO
from pathlib import Path
import zipfile

import numpy as np
import pytest
from starlette.testclient import TestClient

from claude_skills_mcp_backend import http_server


class _DummyModel:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def encode(self, texts, convert_to_numpy=True):
        if convert_to_numpy:
            return np.zeros((len(texts), 4), dtype=np.float32)
        return [[0.0] * 4 for _ in texts]


@pytest.mark.asyncio
async def test_upload_skill_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "claude_skills_mcp_backend.search_engine.SentenceTransformer",
        _DummyModel,
    )

    skills_dir = tmp_path / "skills"
    config_path = tmp_path / "config.json"
    config = {
        "skill_sources": [
            {"type": "local", "path": str(skills_dir)},
        ],
        "embedding_model": "dummy-model",
        "default_top_k": 3,
        "auto_update_enabled": False,
        "load_skill_documents": True,
        "text_file_extensions": [".md", ".py"],
        "allowed_image_extensions": [],
        "max_image_size_bytes": 1024,
    }
    config_path.write_text(json.dumps(config))

    await http_server.initialize_backend(str(config_path))

    assert http_server.loading_state_global is not None
    for _ in range(50):
        if http_server.loading_state_global.is_complete:
            break
        await asyncio.sleep(0.1)
    assert http_server.loading_state_global.is_complete

    app = http_server.get_application()

    skill_content = """---\nname: Example Skill\ndescription: Example description\n---\n# Body\n"""

    zip_bytes = BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        zf.writestr("example-skill/SKILL.md", skill_content)
        zf.writestr("example-skill/scripts/example.py", "print('hello')\n")
    zip_bytes.seek(0)

    files = {"file": ("skill.zip", zip_bytes.read(), "application/zip")}

    with TestClient(app) as client:
        response = client.post("/skills/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Example Skill" in data["skills_added"]

    assert http_server.search_engine is not None
    assert any(skill.name == "Example Skill" for skill in http_server.search_engine.skills)

    if http_server.scheduler_global:
        http_server.scheduler_global.stop()
    http_server.search_engine = None
    http_server.loading_state_global = None
    http_server.update_checker_global = None
    http_server.scheduler_global = None
    http_server.config_global = None
    http_server.reload_lock = None
