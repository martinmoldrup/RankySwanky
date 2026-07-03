---
name: snappylapy
description: 'Create and maintain snapshot tests with Snappylapy for pytest, including fixture usage, foreach-folder test cases, snapshot update flow, and reviewable diffs. Use for unit and integration tests that assert complex or AI-generated outputs.'
argument-hint: 'What should the snapshot test validate (function, module, or pipeline step)?'
user-invocable: true
disable-model-invocation: false
---

# Snappylapy Snapshot Testing

## Outcome
Create reliable, reviewable snapshot tests for Python code that produces complex, nested, or partially non-deterministic outputs.

## Scope
This skill is workspace-scoped and optimized for this repository's pytest setup.

## When to Use
- Add snapshot tests for dictionaries, lists, strings, bytes, or data-like objects.
- Validate integration outputs for pipeline steps without brittle hand-written expected values.
- Build multi-case tests where each case lives in its own folder.
- Review behavior changes by comparing `__test_results__` to `__snapshots__`.
- Update snapshots intentionally after accepted behavior changes.

## Inputs to Collect Before Coding
1. Target under test: function, module entrypoint, or pipeline step.
2. Test level: unit test or integration test.
3. Snapshot shape: full match or partial match strategy.
4. Test data strategy: inline fixtures or folder-based test cases.
5. Update policy: should snapshots be updated in this task or only compared.

## Standard Procedure
1. Place the test in the right test module and import `Expect` (and `LoadSnapshot` when needed).
2. Arrange deterministic setup as much as possible.
3. Run the target logic.
4. Snapshot the relevant output with `expect(...).to_match_snapshot()`.
5. For folder-based cases, use the Snappylapy marker with `foreach_folder_in=...` and include `test_directory: pathlib.Path` in the test signature.
6. Run pytest without snapshot update first and inspect differences.
7. If behavior change is intentional, run with `--snapshot-update` and verify generated snapshot files.
8. Keep `__snapshots__` versioned; keep `__test_results__` ignored.

## Repository-Conformant Test Patterns

### 1) Basic Snapshot Test
Use for deterministic outputs where a full object snapshot is appropriate.

```python
from snappylapy import Expect


def test_transform_output(expect: Expect) -> None:
    result: dict[str, int] = {"a": 1, "b": 2}
    expect.dict(result).to_match_snapshot()
```

### 2) Folder-Per-Case Integration Pattern
Use for many integration cases sharing one test function.

```python
import pathlib
import pytest
import snappylapy
from snappylapy import Expect


TEST_CASES_PATH = pathlib.Path("tests") / "test_cases"


@pytest.mark.integration_test
@snappylapy.marker.configure_snappylapy(foreach_folder_in=TEST_CASES_PATH)
@pytest.mark.asyncio
async def test_main(test_directory: pathlib.Path, expect: Expect) -> None:
    # Arrange input from the current case folder
    # Act by calling the async module under test
    # Assert with snapshot
    expect.dict({"case": test_directory.name}).to_match_snapshot()
```

Important rule:
- The parameter must be named exactly `test_directory` when using `foreach_folder_in`.

### 3) Snapshot Reuse for Downstream Tests
Use `LoadSnapshot` when a later test should consume baseline serialized outputs.

```python
import pytest
from snappylapy import LoadSnapshot


def test_create_snapshot(expect) -> None:
    expect.dict({"id": 123}).to_match_snapshot()


@pytest.mark.snappylapy(depends=[test_create_snapshot])
def test_consume_snapshot(load_snapshot: LoadSnapshot) -> None:
    payload: dict[str, object] = load_snapshot.dict()
    assert "id" in payload
```

## Decision Points
1. If output is stable and deterministic:
Use full snapshot matching.
2. If output includes timestamps, generated IDs, or model text variability:
Normalize/redact volatile fields before snapshot assertion, or compare stable substructures.
3. If many reusable test cases exist in folders:
Use `foreach_folder_in` and `test_directory`.
4. If one snapshot feeds another test:
Use `depends=[...]` plus `LoadSnapshot`.
5. If behavior change is expected and approved:
Run with `--snapshot-update`; otherwise treat diff as regression.

## Update and Review Flow
1. Run tests first without updating snapshots.
2. Inspect failures and compare files in `__test_results__` and `__snapshots__`.
3. Decide whether each difference is expected.
4. Update snapshots only for approved changes.
5. Re-run tests to confirm clean pass after update.

Common commands:
- `pytest -m contains_snapshot --snapshot-details tests/`
- `pytest --snapshot-update`

## Quality Criteria
A snapshot test change is complete when all checks pass:
1. Test name clearly describes behavior, not implementation details.
2. Snapshot assertion covers the behavior contract that matters.
3. Non-deterministic data is handled explicitly.
4. For `foreach_folder_in`, test signature includes `test_directory: pathlib.Path`.
5. `__snapshots__` changes are intentional and reviewable.
6. `__test_results__` is not treated as baseline.
7. Tests pass without requiring unrelated snapshot updates.

## Failure Triage Checklist
1. Did true behavior change, or did setup/environment drift?
2. Are differences only in volatile fields?
3. Is test data loaded from the intended folder/case?
4. Is marker configuration (`integration_test`, `snappylapy`, `asyncio`) correct?
5. Was snapshot update run only after approval?

## Pitfalls to Avoid
- Updating snapshots before inspecting diffs.
- Over-snapshotting giant payloads when only a stable subset is needed.
- Forgetting exact `test_directory` argument name for folder iteration.
- Treating `__test_results__` files as committed baselines.
- Mixing unit and integration concerns in one snapshot test without clear boundaries.

## Done Definition
1. New or updated tests produce stable pass/fail signals.
2. Snapshot files in `__snapshots__` represent intentional expected behavior.
3. Reviewers can understand behavior changes from snapshot diffs.
4. Test execution commands are documented in PR notes or task output.
