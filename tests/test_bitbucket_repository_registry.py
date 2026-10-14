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


def _two_repos(tmp, **first):
    registry = BitbucketRepositoryRegistry(Path(tmp) / "repositories.json")
    registry.create_repository({"id": "one", "workspace": "ws", "repo_slug": "repo-one", **first})
    registry.create_repository({"id": "two", "workspace": "ws", "repo_slug": "repo-two"})
    return registry


def test_allow_merge_defaults_to_false():
    with tempfile.TemporaryDirectory() as tmp:
        registry = _two_repos(tmp)
        assert all(item["allow_merge"] is False for item in registry.list_repositories())


def test_allow_merge_is_isolated_per_repository_and_in_runtime_env():
    with tempfile.TemporaryDirectory() as tmp:
        registry = _two_repos(tmp)
        registry.update_repository("one", {"allow_merge": True})
        assert registry.get_repository("one")["allow_merge"] is True
        assert registry.get_repository("two")["allow_merge"] is False
        # unrelated update keeps the flag
        registry.update_repository("one", {"display_name": "One"})
        assert registry.get_repository("one")["allow_merge"] is True
        items = {item["id"]: item for item in json.loads(registry.runtime_env()["BITBUCKET_REPOSITORIES_JSON"])}
        assert items["one"]["allowMerge"] is True
        assert items["two"]["allowMerge"] is False
        reloaded = BitbucketRepositoryRegistry(Path(tmp) / "repositories.json")
        assert reloaded.get_repository("one")["allow_merge"] is True
        assert reloaded.get_repository("two")["allow_merge"] is False


def test_allow_merge_accepts_strings_and_camel_case():
    with tempfile.TemporaryDirectory() as tmp:
        registry = _two_repos(tmp, allow_merge="true")
        assert registry.get_repository("one")["allow_merge"] is True
        registry.update_repository("one", {"allow_merge": "false"})
        assert registry.get_repository("one")["allow_merge"] is False
        registry.update_repository("two", {"allowMerge": "TRUE"})
        assert registry.get_repository("two")["allow_merge"] is True
        registry.update_repository("two", {"allow_merge": 0})
        assert registry.get_repository("two")["allow_merge"] is False
        registry.update_repository("two", {"allow_merge": 1})
        assert registry.get_repository("two")["allow_merge"] is True


def test_loading_saved_registry_without_allow_merge_defaults_false():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "repositories.json"
        path.write_text(json.dumps({
            "version": 1,
            "default_repository_id": "one",
            "repositories": [{"id": "one", "workspace": "ws", "repo_slug": "repo-one", "status": "active"}],
        }), encoding="utf-8")
        registry = BitbucketRepositoryRegistry(path)
        assert registry.get_repository("one")["allow_merge"] is False
        assert json.loads(registry.runtime_env()["BITBUCKET_REPOSITORIES_JSON"])[0]["allowMerge"] is False
