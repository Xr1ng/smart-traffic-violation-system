import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile, unlink } from 'node:fs/promises'
import { resolve } from 'node:path'

const source = path => readFile(new URL(path, import.meta.url), 'utf8')

test('profile edits backend contact fields and uses role avatars', async () => {
  const profile = await source('../src/views/Profile.vue')
  assert.match(profile, /form\.email/)
  assert.match(profile, /form\.phone/)
  assert.match(profile, /updateProfile\(\{ phone: form\.phone, email: form\.email \}\)/)
  assert.match(profile, /\/images\/admin\.jpg/)
  assert.match(profile, /\/images\/reviewer\.jpg/)
  assert.match(profile, /\/images\/citizen\.jpg/)
  assert.match(profile, /userStore\.logout\(\)/)
  assert.match(profile, /router\.push\('\/login'\)/)
})

test('all layouts use the shared header and route-aware cache shell', async () => {
  const header = await source('../src/components/HeaderActions.vue')
  assert.match(header, /<AnnouncementBell \/>/)
  for (const name of ['AdminLayout', 'ReviewLayout', 'CitizenLayout']) {
    const layout = await source(`../src/layouts/${name}.vue`)
    assert.match(layout, /<HeaderActions/)
    assert.match(layout, /<BackToTop/)
    assert.match(layout, /meta\.keepAlive/)
    assert.doesNotMatch(layout, /cachedViews|:include=/)
  }
})

test('admin placeholders are removed and case detail is shared', async () => {
  const router = await source('../src/router/index.js')
  assert.doesNotMatch(router, /admin\/drivers|admin\/database|DriverList|DatabaseMaintain/)
  assert.match(router, /path: 'violations\/:id'[\s\S]*views\/review\/CaseDetail\.vue/)
  assert.match(router, /keepAlive: true/)
})

test('app provides a global render error boundary', async () => {
  const app = await source('../src/App.vue')
  assert.match(app, /onErrorCaptured/)
  assert.match(app, /window\.location\.reload\(\)/)
})

test('chart theme exposes distinct readable light and dark palettes', async () => {
  const { getChartTheme } = await import('../src/utils/chartTheme.js')
  const light = getChartTheme(false)
  const dark = getChartTheme(true)
  assert.notEqual(light.text, dark.text)
  assert.notEqual(light.grid, dark.grid)
  assert.equal(dark.tooltipBackground, '#1f2329')
})

test('fetchAllPages collects every page without changing filters', async () => {
  const { fetchAllPages } = await import('../src/utils/pagination.js')
  const calls = []
  const rows = await fetchAllPages(async params => {
    calls.push(params)
    return {
      data: {
        items: params.page === 1 ? [{ id: 1 }, { id: 2 }] : [{ id: 3 }],
        total: 3
      }
    }
  }, { plate_no: '川A12345' }, 2)

  assert.deepEqual(rows, [{ id: 1 }, { id: 2 }, { id: 3 }])
  assert.deepEqual(calls, [
    { plate_no: '川A12345', page: 1, page_size: 2 },
    { plate_no: '川A12345', page: 2, page_size: 2 }
  ])
})

test('fetchAllPages returns empty rows and propagates later page failures', async () => {
  const { fetchAllPages } = await import('../src/utils/pagination.js')
  const empty = await fetchAllPages(async () => ({ data: { items: [], total: 0 } }))
  assert.deepEqual(empty, [])

  await assert.rejects(
    fetchAllPages(async ({ page }) => {
      if (page === 2) throw new Error('page failed')
      return { data: { items: [{ id: 1 }], total: 2 } }
    }, {}, 1),
    /page failed/
  )
})

test('exportToExcel writes one formatted worksheet with explicit columns', async () => {
  const XLSX = (await import('xlsx')).default
  const { exportToExcel, formatExportTime } = await import('../src/utils/export.js')
  const target = resolve('.tmp-selective-export')
  try {
    exportToExcel(
      [{ plate: '川A12345', points: 3 }],
      [
        { key: 'plate', label: '车牌号', width: 16 },
        { key: 'points', label: '扣分', width: 10 }
      ],
      target
    )
    const workbook = XLSX.readFile(`${target}.xlsx`)
    assert.deepEqual(workbook.SheetNames, ['Sheet1'])
    assert.deepEqual(XLSX.utils.sheet_to_json(workbook.Sheets.Sheet1, { header: 1 }), [
      ['车牌号', '扣分'],
      ['川A12345', '3']
    ])
  } finally {
    await unlink(`${target}.xlsx`).catch(() => {})
  }

  assert.equal(formatExportTime(null), '')
  assert.equal(
    formatExportTime('2026-07-14T10:20:30'),
    new Date('2026-07-14T10:20:30').toLocaleString('zh-CN')
  )
})

test('violation and report pages export every matching page', async () => {
  const violationApi = await source('../src/api/violation.js')
  assert.match(violationApi, /fetchOwnerViolations = \(ownerId, params\)/)
  assert.match(violationApi, /owners\/\$\{ownerId\}\/violations`.*, \{ params \}/s)

  for (const path of [
    '../src/views/admin/ViolationList.vue',
    '../src/views/review/ViolationList.vue',
    '../src/views/citizen/MyViolations.vue',
    '../src/views/citizen/MyReports.vue'
  ]) {
    const page = await source(path)
    assert.match(page, /fetchAllPages/)
    assert.match(page, /exportToExcel/)
    assert.match(page, /exporting/)
    assert.match(page, /:disabled="total === 0"/)
  }

  const reports = await source('../src/views/citizen/MyReports.vue')
  assert.match(reports, /fetchAllPages\(params => fetchCases\(params\)/)
})

test('vehicle management selects citizen owners by username', async () => {
  const vehicles = await source('../src/views/admin/VehicleList.vue')
  assert.match(vehicles, /import \{ fetchUsers \} from '@\/api\/system'/)
  assert.match(vehicles, /import \{ fetchAllPages \} from '@\/utils\/pagination'/)
  assert.match(vehicles, /\{ role: 'citizen' \}/)
  assert.match(vehicles, /:data="displayedVehicles"/)
  assert.match(vehicles, /prop="owner_name"/)
  assert.match(vehicles, /<el-select[\s\S]*v-model="form\.owner_id"[\s\S]*filterable[\s\S]*clearable/)
  assert.doesNotMatch(vehicles, /<el-input-number[\s\S]*v-model="form\.owner_id"/)
})

test('batch reject sends the exact payload and reports partial failure', async () => {
  const { batchRejectCases } = await import('../src/utils/batchReject.js')
  const calls = []
  const result = await batchRejectCases([1, 2, 1], ' 证据不足 ', async (id, payload) => {
    calls.push([id, payload])
    if (id === 2) throw new Error('failed')
  })

  assert.deepEqual(calls, [
    [1, { reject_reason: '证据不足' }],
    [2, { reject_reason: '证据不足' }]
  ])
  assert.deepEqual(result, { succeededIds: [1], failedIds: [2] })
})

test('batch reject requires a reason and workbench has no batch approve', async () => {
  const { batchRejectCases } = await import('../src/utils/batchReject.js')
  await assert.rejects(
    batchRejectCases([1], '   ', async () => {}),
    TypeError
  )

  const workbench = await source('../src/views/review/Workbench.vue')
  assert.match(workbench, /batchRejectCases/)
  assert.match(workbench, /\['uploaded', 'pending_human_review'\]/)
  assert.match(workbench, /rejectCase/)
  assert.doesNotMatch(workbench, /batchApprove|批量通过/)
})

test('announcement administration uses backend CRUD without publish state', async () => {
  const announcement = await source('../src/views/admin/Announcement.vue')
  for (const api of [
    'fetchAnnouncements',
    'createAnnouncement',
    'updateAnnouncement',
    'deleteAnnouncement'
  ]) {
    assert.match(announcement, new RegExp(api))
  }
  assert.match(announcement, /buildAnnouncementPayload\(form\)/)
  assert.match(announcement, /<el-pagination/)
  assert.match(announcement, /openEdit/)
  assert.match(announcement, /removeAnnouncement/)
  assert.doesNotMatch(announcement, /UnderDevelopment|localStorage|is_published/)
})

test('rule administration UI and API are removed', async () => {
  const api = await source('../src/api/system.js')
  const router = await source('../src/router/index.js')
  const layout = await source('../src/layouts/AdminLayout.vue')
  assert.doesNotMatch(api, /admin\/rules|fetchRules|createRule|updateRule|deleteRule/)
  assert.doesNotMatch(router, /AdminRules|RuleConfig|path: 'rules'/)
  assert.doesNotMatch(layout, /\/admin\/rules|违章规则/)
  assert.match(
    layout,
    /<el-menu-item index="\/admin\/announcements"[\s\S]*?<el-icon><Bell \/><\/el-icon>[\s\S]*?<template #title>公告管理<\/template>[\s\S]*?<\/el-menu-item>/
  )
  assert.doesNotMatch(layout, /<el-sub-menu index="configuration"|系统配置|<Tools \/>/)
})

test('all role layouts collapse the sidebar when entering a mobile viewport', async () => {
  const responsiveSidebar = await source('../src/composables/useResponsiveSidebar.js')
  assert.match(responsiveSidebar, /matchMedia\('\(max-width: 720px\)'\)/)
  assert.match(responsiveSidebar, /if \(event\.matches\) isCollapse\.value = true/)
  assert.match(responsiveSidebar, /addEventListener\('change'/)
  assert.match(responsiveSidebar, /removeEventListener\('change'/)

  for (const name of ['AdminLayout', 'ReviewLayout', 'CitizenLayout']) {
    const layout = await source(`../src/layouts/${name}.vue`)
    assert.match(layout, /useResponsiveSidebar/)
    assert.match(layout, /const \{ isCollapse \} = useResponsiveSidebar\(\)/)
  }
})

test('review workbench stacks filters and cards on mobile', async () => {
  const workbench = await source('../src/views/review/Workbench.vue')
  assert.match(workbench, /class="status-filter"/)
  assert.match(workbench, /class="source-filter"/)
  assert.match(workbench, /class="keyword-filter"/)
  assert.doesNotMatch(workbench, /margin-left:12px/)
  assert.match(workbench, /@media \(max-width: 720px\)/)
  assert.match(workbench, /\.toolbar\s*\{\s*flex-direction: column;/)
  assert.match(workbench, /\.card-grid\s*\{\s*grid-template-columns: minmax\(0, 1fr\);/)
})

test('workbench thumbnails navigate without opening a cached image viewer', async () => {
  const workbench = await source('../src/views/review/Workbench.vue')
  const detail = await source('../src/views/review/CaseDetail.vue')

  assert.doesNotMatch(workbench, /preview-src-list/)
  assert.match(detail, /preview-src-list/)
})

test('dashboard stacks its primary charts on mobile', async () => {
  const dashboard = await source('../src/views/stats/Dashboard.vue')
  assert.doesNotMatch(dashboard, /<el-col :span="8">/)
  assert.equal(
    (dashboard.match(/<el-col :xs="24" :sm="24" :md="8">/g) || []).length,
    3
  )
})

test('workbench checkboxes bind scalar checked state without Vue warnings', async () => {
  const workbench = await source('../src/views/review/Workbench.vue')
  assert.doesNotMatch(workbench, /v-model="selectedIds"/)
  assert.match(workbench, /:model-value="selectedIds\.includes\(item\.id\)"/)
  assert.match(workbench, /@update:model-value="checked => toggleCaseSelection\(item\.id, checked\)"/)
  assert.match(workbench, /function toggleCaseSelection\(id, checked\)/)
})

test('workbench card headers contain long case metadata on mobile', async () => {
  const workbench = await source('../src/views/review/Workbench.vue')
  assert.match(workbench, /\.card-header\s*\{[^}]*min-width: 0;/s)
  assert.match(workbench, /\.case-no,\s*\.case-source\s*\{[^}]*overflow-wrap: anywhere;/s)
  assert.match(workbench, /@media \(max-width: 720px\)[\s\S]*\.card-header\s*\{\s*flex-wrap: wrap;/)
  assert.match(workbench, /\.case-source\s*\{\s*flex: 1 0 100%;/)
})
