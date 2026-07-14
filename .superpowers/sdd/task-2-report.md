# Task 2 Report: Authenticated Announcement API

## Status

Complete. Authenticated users can list and read announcements, while only
administrators can create, update, and delete them.

## Implementation

- Added a public `/api/v1/announcements` router protected by
  `get_current_user` for paginated list and detail reads.
- Added an `/api/v1/admin/announcements` router protected by
  `require_role("admin")` for POST, PATCH, and DELETE operations.
- Passed the authenticated administrator ID to every write service call so
  Task 1 audit records identify the exact actor.
- Returned the Task 1 response schemas and an explicit empty `204 Response`
  for deletion.
- Registered both routers without changing unrelated route behavior.
- Covered citizen, reviewer, administrator, and unauthenticated access; input
  validation; partial updates; missing resources; stable pagination; response
  bodies; and exact audit actions.

## Files

- Created `backend/app/api/v1/announcements.py`
- Modified `backend/app/api/v1/router.py`
- Created `backend/tests/api/test_announcements_api.py`
- Created `.superpowers/sdd/task-2-report.md`

## TDD Evidence

### RED

Command:

```powershell
D:\@DevCode\Code_Python\交通违章智能管理平台\backend\.venv\Scripts\python.exe -m pytest tests/api/test_announcements_api.py -v --basetemp=.tmp\pytest-task2
```

Result: `20 failed, 2 passed, 1 warning in 9.22s`.

The failures were the expected route-level `404 Not Found` responses because
the announcement routers were not registered. The two status-only missing
update/delete cases initially also received `404` from the absent route; their
assertions were tightened before implementation to require the Task 1 service
detail `{"detail": "公告不存在"}`.

### Focused GREEN

Command:

```powershell
D:\@DevCode\Code_Python\交通违章智能管理平台\backend\.venv\Scripts\python.exe -m pytest tests/api/test_announcements_api.py tests/services/test_announcement_service.py -v --basetemp=.tmp\pytest-task2
```

Result: `38 passed, 1 warning in 11.93s`.

An independent review subsequently requested explicit coverage for
unauthenticated administrator writes and an authenticated missing public
detail. Those assertions were added without production changes and are
included in the full-suite result below.

## Full Backend Verification

Command:

```powershell
D:\@DevCode\Code_Python\交通违章智能管理平台\backend\.venv\Scripts\python.exe -m pytest -v --basetemp=.tmp\pytest-task2
```

Result: `291 passed, 1 warning in 46.98s`.

An initial invocation of this same command was terminated by the command
wrapper after 1.574 seconds because its timeout was mistakenly set to one
second; it produced no usable pytest result. The command above is the complete
fresh verification run.

## Self-Review

- Confirmed public reads require authentication and accept citizen, reviewer,
  and administrator roles.
- Confirmed every write rejects unauthenticated users with `401`, rejects
  citizen/reviewer users with `403`, and uses the authenticated administrator
  as the audit actor.
- Confirmed schema validation handles blank, oversized, and empty PATCH input.
- Confirmed PATCH preserves omitted content, pagination uses the stable Task 1
  ordering, missing resources return the service `404`, and DELETE has no body.
- Confirmed Task 1 model/schema/service files are unchanged.
- `git diff --check` passed.
- Independent read-only review found no Critical, Important, or Minor issues
  and assessed the change ready to merge after full verification.

## Concerns

No implementation concerns. The full suite emits the single pre-existing
Starlette `httpx` deprecation warning documented in the baseline.
