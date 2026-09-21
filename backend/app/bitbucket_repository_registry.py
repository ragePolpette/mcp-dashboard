"""Persistent registry for Bitbucket MCP repositories."""

from __future__ import annotations

import copy
import json
import re
import threading
from pathlib import Path
from typing import Any


class BitbucketRepositoryRegistry:
    def __init__(self, state_path: Path) -> None:
        self.state_path = Path(state_path)
        self._lock = threading.RLock()
        self._repositories: list[dict[str, Any]] = []
        self._default_repository_id = ""
        self._load()

    def _load(self) -> None:
        if not self.state_path.exists():
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return
        repositories = payload.get("repositories") if isinstance(payload, dict) else None
        if not isinstance(repositories, list):
            return
        self._repositories = [self._normalize(item) for item in repositories]
        if len({item["id"] for item in self._repositories}) != len(self._repositories):
            raise ValueError("Duplicate repository id in saved registry.")
        default_id = str(payload.get("default_repository_id") or "").strip()
        self._default_repository_id = default_id if self._active(default_id) else ""

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "default_repository_id": self._default_repository_id,
            "repositories": self._repositories,
        }
        self.state_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _normalize(self, raw: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
        source = copy.deepcopy(existing or {})
        source.update(raw or {})
        repository_id = str(source.get("id") or "").strip()
        workspace = str(source.get("workspace") or "").strip()
        repo_slug = str(source.get("repo_slug") or source.get("repoSlug") or "").strip()
        for label, value in (("id", repository_id), ("workspace", workspace), ("repo_slug", repo_slug)):
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
                raise ValueError(f"{label} must start with a letter or digit and contain only letters, digits, _, - or .")
        status = str(source.get("status") or "active").strip().lower()
        if status not in {"active", "disabled"}:
            raise ValueError("status must be active or disabled.")
        return {
            "id": repository_id,
            "display_name": str(source.get("display_name") or repository_id).strip() or repository_id,
            "workspace": workspace,
            "repo_slug": repo_slug,
            "default_destination_branch": str(source.get("default_destination_branch") or "").strip(),
            "status": status,
        }

    def _index(self, repository_id: str) -> int:
        return next((index for index, item in enumerate(self._repositories) if item["id"] == repository_id), -1)

    def _active(self, repository_id: str) -> bool:
        return any(item["id"] == repository_id and item["status"] == "active" for item in self._repositories)

    def list_repositories(self) -> list[dict[str, Any]]:
        with self._lock:
            return [{**copy.deepcopy(item), "is_default": item["id"] == self._default_repository_id} for item in self._repositories]

    def get_repository(self, repository_id: str) -> dict[str, Any] | None:
        with self._lock:
            index = self._index(repository_id)
            return None if index < 0 else {**copy.deepcopy(self._repositories[index]), "is_default": repository_id == self._default_repository_id}

    def create_repository(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            repository = self._normalize(payload)
            if self._index(repository["id"]) >= 0:
                raise ValueError(f"Duplicate repository id: {repository['id']}")
            self._repositories.append(repository)
            if payload.get("is_default") is True or not self._default_repository_id:
                self._default_repository_id = repository["id"] if repository["status"] == "active" else ""
            self._save()
            return self.get_repository(repository["id"])

    def update_repository(self, repository_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            index = self._index(repository_id)
            if index < 0:
                raise ValueError(f"Unknown repository id: {repository_id}")
            repository = self._normalize({**payload, "id": repository_id}, self._repositories[index])
            self._repositories[index] = repository
            if payload.get("is_default") is True:
                if repository["status"] != "active":
                    raise ValueError("A disabled repository cannot be the default.")
                self._default_repository_id = repository_id
            elif repository_id == self._default_repository_id and repository["status"] != "active":
                self._default_repository_id = ""
            self._save()
            return self.get_repository(repository_id)

    def runtime_env(self) -> dict[str, str]:
        with self._lock:
            repositories = [
                {
                    "id": item["id"],
                    "displayName": item["display_name"],
                    "workspace": item["workspace"],
                    "repoSlug": item["repo_slug"],
                    "defaultDestinationBranch": item["default_destination_branch"],
                    "status": item["status"],
                }
                for item in self._repositories
            ]
            return {
                "BITBUCKET_REPOSITORIES_JSON": json.dumps(repositories, ensure_ascii=True, separators=(",", ":")),
                "BITBUCKET_DEFAULT_REPOSITORY": self._default_repository_id,
            }
