"""Source/test commit provenance captured before evidence output is created."""

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


SOURCE_COMMIT_ENV = "RXCARE_SOURCE_COMMIT"
_COMMIT_PATTERN = re.compile(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})")


def _explicit_source_commit(value: Optional[str]) -> Optional[str]:
    candidate = value if value is not None else os.environ.get(SOURCE_COMMIT_ENV)
    if candidate is None:
        return None
    candidate = candidate.strip()
    if not _COMMIT_PATTERN.fullmatch(candidate):
        raise ValueError(
            f"{SOURCE_COMMIT_ENV} must contain a full 40- or 64-character "
            "hexadecimal Git commit ID"
        )
    return candidate.lower()


def capture_source_control_context(
    repository_root: Path,
    explicit_commit: Optional[str] = None,
) -> Dict[str, Any]:
    """Capture source/test revision state before an evidence path is created.

    A detached staging copy may not contain ``.git`` metadata. In that case an
    explicit commit can be supplied through ``RXCARE_SOURCE_COMMIT`` (or the
    function argument), while the unavailable working-tree state remains
    stated rather than invented.
    """

    override = _explicit_source_commit(explicit_commit)
    base: Dict[str, Any] = {
        "source_test_context_captured_before_evidence": True,
        "final_release_commit_sha": None,
        "final_release_tag": None,
        "release_provenance_note": (
            "source_test_commit_sha identifies the code and tests used for "
            "this evidence run; the final release commit/tag is assigned "
            "after immutable evidence is added."
        ),
    }

    try:
        top_level = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=repository_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if top_level.returncode != 0:
            return {
                **base,
                "source_test_commit_sha": override,
                "source_test_commit_origin": (
                    "explicit_override" if override else "unavailable"
                ),
                "source_test_working_tree": (
                    "not available in this staging copy"
                ),
                "source_test_changed_path_count": None,
            }

        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip().lower()
        if override and revision != override:
            raise ValueError(
                f"{SOURCE_COMMIT_ENV} does not match the checked-out HEAD"
            )
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", "."],
            cwd=repository_root,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.splitlines()
        return {
            **base,
            "source_test_commit_sha": revision,
            "source_test_commit_origin": (
                "git_head_verified_by_override" if override else "git_head"
            ),
            "source_test_working_tree": "dirty" if status else "clean",
            "source_test_changed_path_count": len(status),
        }
    except (OSError, subprocess.SubprocessError) as error:
        return {
            **base,
            "source_test_commit_sha": override,
            "source_test_commit_origin": (
                "explicit_override" if override else "unavailable"
            ),
            "source_test_working_tree": "unavailable",
            "source_test_changed_path_count": None,
            "source_test_context_diagnostic": type(error).__name__,
        }
