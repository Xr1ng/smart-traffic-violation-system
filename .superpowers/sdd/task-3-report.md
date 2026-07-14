# Task 3 Report: Frontend Announcement Contract and Shared Header Entry

## Files

- Created `smart-traffic-frontend/src/api/announcement.js`
- Created `smart-traffic-frontend/src/components/AnnouncementBell.vue`
- Updated `smart-traffic-frontend/src/utils/contracts.js`
- Updated `smart-traffic-frontend/tests/contracts.test.js`
- Updated `smart-traffic-frontend/src/layouts/CitizenLayout.vue`
- Updated `smart-traffic-frontend/src/layouts/ReviewLayout.vue`
- Updated `smart-traffic-frontend/src/layouts/AdminLayout.vue`

## TDD Evidence

### RED

Command: `cd smart-traffic-frontend; npm test`

Result: exit 1, 32 passed and 2 failed. The failures were the expected missing-feature failures:

- `TypeError: contracts.buildAnnouncementPayload is not a function`
- `ENOENT` for `src/api/announcement.js`

### GREEN

Command: `cd smart-traffic-frontend; npm test`

Result: exit 0, 34 passed and 0 failed.

The new coverage verifies payload trimming and field selection, all five exact API method/path contracts, the latest-five request, the accessible Element Plus bell entry without a badge, and mounting in all three shared layouts.

## Build

Command: `cd smart-traffic-frontend; npm run build`

Result: exit 0. Vite transformed 2,277 modules and completed the production build. Output retained the baseline `@vueuse` PURE-comment and chunk-size warnings.

## Self-Review

- API functions use the existing Axios wrapper and exact Task 2 routes.
- The payload helper emits only trimmed `title` and `content` fields.
- Opening the popover refreshes page 1 with `page_size: 5`; selecting a row fetches full detail.
- Request failures are left to the shared Axios interceptor; the component does not import or call `ElMessage`.
- The trigger has a stable 32 by 32 pixel footprint, an Element Plus `Bell`, tooltip, and `aria-label`; no unread state or badge exists.
- The popover is constrained to the viewport, the list/loading/empty surface has fixed height, and long titles/content wrap without overlapping. Detail content preserves body whitespace in a scrollable responsive dialog.
- `AnnouncementBell` appears immediately before the theme toggle in Citizen, Review, and Admin layouts.
- `git diff --check` completed without whitespace errors.

## Concerns

- No task-specific concerns. The production build continues to report the two known categories of baseline warnings noted above.
