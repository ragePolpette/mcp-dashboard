from __future__ import annotations

import json
from pathlib import Path
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.bitbucket_repository_registry import BitbucketRepositoryRegistry


def test_registry_supports_multiple_repositories_and_default():
    with tempfile.TemporaryDirectory() as tmp:
        registry = BitbucketRepositoryRegistry(Path(tmp) / "repositories.json")
        registry.create_repository({"id": "one", "workspace": "ws", "repo_slug": "repo-one", "is_default": True})
        registry.create_repository({"id": "two", "workspace": "ws", "repo_slug": "repo-two"})

        repositories = registry.list_repositories()
        assert len(repositories) == 2
        assert repositories[0]["is_default"] is True
        runtime = registry.runtime_env()
        assert runtime["BITBUCKET_DEFAULT_REPOSITORY"] == "one"
        assert [item["id"] for item in json.loads(runtime["BITBUCKET_REPOSITORIES_JSON"])] == ["one", "two"]


def test_registry_rejects_duplicates_and_clears_disabled_default():
    with tempfile.TemporaryDirectory() as tmp:
        registry = BitbucketRepositoryRegistry(Path(tmp) / "repositories.json")
        registry.create_repository({"id": "one", "workspace": "ws", "repo_slug": "repo-one", "is_default": True})
        try:
            registry.create_repository({"id": "one", "workspace": "ws", "repo_slug": "other"})
            raise AssertionError("duplicate repository accepted")
        except ValueError as exc:
            assert "Duplicate" in str(exc)
        registry.update_repository("one", {"status": "disabled"})
        assert registry.runtime_env()["BITBUCKET_DEFAULT_REPOSITORY"] == ""
