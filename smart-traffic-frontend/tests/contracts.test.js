import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { loadConfigFromFile } from 'vite'
import * as contracts from '../src/utils/contracts.js'
import {
  buildApprovePayload,
  buildRejectPayload,
  buildReportHistoryQuery,
  buildReportRequest,
  buildReportRoute,
  buildViolationQuery,
  caseAiFallbackText,
  fetchAllCitizenCases,
  getCaseReviewOpinion,
  getStatisticsCards,
  isApprovedCaseStatus,
  mapNamedSeries,
  reportPathForRoute,
  summarizeCitizenOverview
} from '../src/utils/contracts.js'

test('proxies API and media requests to the configured backend target', async () => {
  const previousTarget = process.env.VITE_API_PROXY_TARGET
  const configPath = fileURLToPath(new URL('../vite.config.js', import.meta.url))
  const expectedTarget = 'http://127.0.0.1:9123'

  try {
    delete process.env.VITE_API_PROXY_TARGET
    const defaultConfig = await loadConfigFromFile(
      { command: 'serve', mode: 'test' },
      configPath
    )
    assert.equal(defaultConfig.config.server.proxy['/api'].target, 'http://127.0.0.1:8000')
    assert.equal(defaultConfig.config.server.proxy['/media'].target, 'http://127.0.0.1:8000')

    process.env.VITE_API_PROXY_TARGET = expectedTarget
    const configured = await loadConfigFromFile(
      { command: 'serve', mode: 'test' },
      configPath
    )
    const proxy = configured.config.server.proxy

    assert.equal(proxy['/api'].target, expectedTarget)
    assert.equal(proxy['/media'].target, expectedTarget)
    assert.equal(proxy['/media'].changeOrigin, true)
    assert.equal(proxy['/media'].rewrite, undefined)
  } finally {
    if (previousTarget === undefined) {
      delete process.env.VITE_API_PROXY_TARGET
    } else {
      process.env.VITE_API_PROXY_TARGET = previousTarget
    }
  }
})

test('maps backend statistics fields without multiplying percentages', () => {
  const cards = getStatisticsCards({
    total_cases: 3,
    total_violations: 2,
    approve_rate: 66.7,
    reject_rate: 33.3,
    pending_count: 1,
    today_new: 2
  })

  assert.deepEqual(cards.map(card => card.value), [3, 2, '66.7%', '33.3%', 1, 2])
})

test('maps name/value statistic series', () => {
  assert.deepEqual(
    mapNamedSeries({ items: [{ name: '超速', value: 2 }] }),
    [{ name: '超速', value: 2 }]
  )
})

test('uses backend violation query names', () => {
  assert.deepEqual(buildViolationQuery({
    plate: '粤A',
    type: '超速',
    location: '人民路',
    dateRange: ['2026-07-01', '2026-07-10']
  }, 2, 10), {
    page: 2,
    page_size: 10,
    plate_no: '粤A',
    violation_type: '超速',
    location_text: '人民路',
    start_time: '2026-07-01T00:00:00',
    end_time: '2026-07-10T23:59:59'
  })
})

test('omits empty violation filters from the query', () => {
  assert.deepEqual(buildViolationQuery({
    plate: '',
    type: '',
    status: ''
  }, 1, 10), {
    page: 1,
    page_size: 10
  })
})

test('builds vehicle queries with only the backend plate filter', () => {
  assert.deepEqual(contracts.buildVehicleQuery({
    plate: ' 粤A12345 ',
    brand: '不存在的字段'
  }, 2, 20), {
    page: 2,
    page_size: 20,
    plate_no: '粤A12345'
  })
})

test('omits an empty vehicle plate filter from the query', () => {
  assert.deepEqual(contracts.buildVehicleQuery({ plate: '   ' }, 1, 10), {
    page: 1,
    page_size: 10
  })
})

test('builds vehicle payloads with only schema fields and normalized blanks', () => {
  assert.deepEqual(contracts.buildVehiclePayload({
    plate_no: ' 粤B54321 ',
    owner_id: '',
    vehicle_type: ' ',
    color: ' 白色 ',
    brand: '不存在的字段'
  }), {
    plate_no: '粤B54321',
    owner_id: null,
    vehicle_type: null,
    color: '白色'
  })
})

test('builds exact user create payloads', () => {
  assert.deepEqual(contracts.buildUserCreatePayload({
    id: 99,
    username: ' reviewer2 ',
    password: 'secret123',
    phone: '',
    email: ' reviewer2@example.com ',
    role_code: 'reviewer',
    status: 'disabled'
  }), {
    username: 'reviewer2',
    password: 'secret123',
    phone: null,
    email: 'reviewer2@example.com',
    role_code: 'reviewer'
  })
})

test('omits username and blank passwords from user update payloads', () => {
  assert.deepEqual(contracts.buildUserUpdatePayload({
    username: 'immutable-name',
    password: '   ',
    phone: '',
    email: ' user@example.com ',
    role_code: 'citizen',
    status: 'disabled',
    created_at: '2026-07-10T00:00:00'
  }), {
    phone: null,
    email: 'user@example.com',
    role_code: 'citizen',
    status: 'disabled'
  })
})

test('persists the new switch status without reversing it', async () => {
  const row = { id: 7, status: 'active' }
  let submitted

  const saved = await contracts.persistUserStatus(row, 'active', async (id, payload) => {
    submitted = { id, payload }
  })

  assert.equal(saved, true)
  assert.deepEqual(submitted, { id: 7, payload: { status: 'active' } })
  assert.equal(row.status, 'active')
})

test('rolls the switch status back when persistence fails', async () => {
  const row = { id: 8, status: 'disabled' }

  const saved = await contracts.persistUserStatus(row, 'disabled', async () => {
    throw new Error('request failed')
  })

  assert.equal(saved, false)
  assert.equal(row.status, 'active')
})

test('builds exact review request bodies', () => {
  const form = {
    action: 'approve',
    plate_no: '粤A1',
    violation_type: '超速',
    fine_amount: 200,
    points: 3,
    review_opinion: '证据清晰'
  }

  assert.deepEqual(buildApprovePayload(form), {
    plate_no: '粤A1',
    violation_type: '超速',
    fine_amount: 200,
    points: 3,
    review_opinion: '证据清晰'
  })
  assert.deepEqual(buildRejectPayload(form), { reject_reason: '证据清晰' })
})

test('keeps admin report navigation inside admin routes', () => {
  assert.equal(reportPathForRoute('/admin/stats'), '/admin/stats/report')
  assert.equal(reportPathForRoute('/stats'), '/stats/report')
})

test('carries the selected full-day range into the report route', () => {
  const route = buildReportRoute('/admin/stats', [
    new Date('2026-07-01T08:30:00+08:00'),
    new Date('2026-07-31T12:00:00+08:00')
  ])

  assert.equal(route.path, '/admin/stats/report')
  assert.deepEqual(route.query, {
    start_time: '2026-06-30T16:00:00.000Z',
    end_time: '2026-07-31T15:59:59.999Z'
  })
  assert.deepEqual(buildReportRequest([
    new Date('2026-07-01T08:30:00+08:00'),
    new Date('2026-07-31T12:00:00+08:00')
  ]), route.query)
})

test('builds paged history queries with an independent full-day filter', () => {
  assert.deepEqual(buildReportHistoryQuery([], 2, 20), {
    page: 2,
    page_size: 20
  })
  assert.deepEqual(buildReportHistoryQuery([
    new Date('2026-07-01T10:00:00+08:00'),
    new Date('2026-07-15T12:00:00+08:00')
  ], 3, 10), {
    page: 3,
    page_size: 10,
    start_time: '2026-06-30T16:00:00.000Z',
    end_time: '2026-07-15T15:59:59.999Z'
  })
})

test('describes missing AI results according to case processing state', () => {
  assert.equal(caseAiFallbackText('detecting'), 'AI 处理中...')
  assert.equal(caseAiFallbackText('ai_reviewing'), 'AI 处理中...')

  for (const status of ['uploaded', 'pending_human_review', 'approved', 'rejected', 'notified']) {
    assert.equal(caseAiFallbackText(status), '暂无 AI 结果')
  }
})

test('loads every case media URL through the authenticated media loader', async () => {
  const requested = []
  const media = await contracts.loadProtectedMediaUrls({
    original_url: '/media/original.jpg',
    annotated_url: '/media/annotated.jpg'
  }, async url => {
    requested.push(url)
    return `blob:${url}`
  })

  assert.deepEqual(requested, ['/media/original.jpg', '/media/annotated.jpg'])
  assert.deepEqual(media, {
    original_url: 'blob:/media/original.jpg',
    annotated_url: 'blob:/media/annotated.jpg'
  })

  assert.equal(
    contracts.mediaPathToApiPath('/media/evidence name.jpg'),
    '/media/evidence%20name.jpg'
  )
  assert.throws(() => contracts.mediaPathToApiPath('/other/evidence.jpg'))
})

test('keeps a case visible when protected media cannot be loaded', async () => {
  const media = await contracts.loadProtectedMediaUrls(
    { original_url: '/media/missing.jpg' },
    async () => { throw new Error('missing') }
  )

  assert.deepEqual(media, { original_url: null })
})

test('releases generated media object URLs', () => {
  const released = []
  contracts.releaseProtectedMediaUrls({
    original_url: 'blob:one',
    annotated_url: null,
    external_url: 'https://example.com/evidence.jpg'
  }, url => released.push(url))

  assert.deepEqual(released, ['blob:one'])
})

test('accepts only the latest active protected-media request', () => {
  const guard = contracts.createLatestRequestGuard()
  const first = guard.begin()
  const second = guard.begin()

  assert.equal(guard.isCurrent(first), false)
  assert.equal(guard.isCurrent(second), true)

  guard.invalidate()
  assert.equal(guard.isCurrent(second), false)
})

test('maps notified cases and nested review results to the approved terminal view', () => {
  assert.equal(isApprovedCaseStatus('approved'), true)
  assert.equal(isApprovedCaseStatus('notified'), true)
  assert.equal(isApprovedCaseStatus('rejected'), false)
  assert.equal(
    getCaseReviewOpinion({ review: { review_opinion: '证据清晰' } }),
    '证据清晰'
  )
  assert.equal(getCaseReviewOpinion({}), '')
})

test('summarizes citizen overview from real API payloads', () => {
  assert.deepEqual(summarizeCitizenOverview(
    { total: 2 },
    { total: 3, items: [{ reward: 10 }, { reward: null }, { reward: 5 }] },
    { total: 1 }
  ), { violations: 2, reports: 3, rewards: 15, vehicles: 1 })
})

test('includes rewards from every citizen case page when total exceeds 100', async () => {
  const requestedPages = []
  const cases = await fetchAllCitizenCases(async ({ page }) => {
    requestedPages.push(page)
    if (page === 1) {
      return {
        total: 101,
        page: 1,
        page_size: 100,
        items: Array.from({ length: 100 }, () => ({ reward: 1 }))
      }
    }
    return { total: 101, page: 2, page_size: 100, items: [{ reward: 5 }] }
  })

  assert.deepEqual(requestedPages, [1, 2])
  assert.deepEqual(
    summarizeCitizenOverview({}, cases, {}),
    { violations: 0, reports: 101, rewards: 105, vehicles: 0 }
  )
})

test('does not fabricate citizen announcements without a backend API', async () => {
  const source = await readFile(new URL('../src/views/citizen/Home.vue', import.meta.url), 'utf8')

  assert.doesNotMatch(source, /系统升级通知/)
  assert.match(source, /const announcements = ref\(\[\]\)/)
})

test('reviewer violations use the shared query contract without duplicate errors or fake exports', async () => {
  const source = await readFile(new URL('../src/views/review/ViolationList.vue', import.meta.url), 'utf8')
  const apiSource = await readFile(new URL('../src/api/violation.js', import.meta.url), 'utf8')

  assert.match(source, /buildViolationQuery\(filter, page\.value, pageSize\.value\)/)
  assert.doesNotMatch(source, /导出 Excel|handleExport|ElMessage/)
  assert.doesNotMatch(source, /prop="owner_name"|label="车主"/)
  assert.doesNotMatch(apiSource, /exportExcel|导出成功/)
})

test('workbench finishes fallible count requests before creating media object URLs', async () => {
  const source = await readFile(new URL('../src/views/review/Workbench.vue', import.meta.url), 'utf8')

  assert.ok(source.indexOf('const [uploadedRes, pendingRes]') >= 0)
  assert.ok(source.indexOf('const nextCases = await Promise.all') >= 0)
  assert.ok(
    source.indexOf('const [uploadedRes, pendingRes]') <
      source.indexOf('const nextCases = await Promise.all')
  )
})

test('admin vehicles expose only backend vehicle fields and supported actions', async () => {
  const source = await readFile(new URL('../src/views/admin/VehicleList.vue', import.meta.url), 'utf8')

  for (const field of ['id', 'plate_no', 'owner_id', 'vehicle_type', 'color', 'created_at']) {
    assert.match(source, new RegExp(`prop="${field}"|form\\.${field}`))
  }
  assert.match(source, /buildVehicleQuery/)
  assert.match(source, /buildVehiclePayload/)
  assert.doesNotMatch(
    source,
    /plate_number|owner_name|owner_phone|engine_number|prop="(?:brand|model)"|form\.(?:brand|model)/
  )
  assert.doesNotMatch(source, /详情|删除|viewDetail|handleDelete|deleteVehicle/)
})

test('admin users require a create-only password and remove fake deletion', async () => {
  const source = await readFile(new URL('../src/views/admin/UserManage.vue', import.meta.url), 'utf8')

  assert.match(source, /v-if="!dialog\.isEdit"[^>]*label="密码"/)
  assert.match(source, /buildUserCreatePayload/)
  assert.match(source, /buildUserUpdatePayload/)
  assert.match(source, /@change="newStatus => toggleStatus\(row, newStatus\)"/)
  assert.match(source, /persistUserStatus/)
  assert.doesNotMatch(source, /删除|deleteUser|ElMessageBox/)
})

test('admin violations keep real actions and remove fake bulk and delete operations', async () => {
  const source = await readFile(new URL('../src/views/admin/ViolationList.vue', import.meta.url), 'utf8')

  assert.match(source, /\/admin\/violations\/upload/)
  assert.match(source, /\/review\/case\/\$\{row\.case_id\}/)
  assert.doesNotMatch(source, /selection|selectedIds|handleSelectionChange/)
  assert.doesNotMatch(source, /批量导出|handleBatchExport|handleDelete|确定删除/)
})

test('AI report page generates only on user action and supports print export', async () => {
  const source = await readFile(new URL('../src/views/stats/Report.vue', import.meta.url), 'utf8')
  const dashboardSource = await readFile(new URL('../src/views/stats/Dashboard.vue', import.meta.url), 'utf8')
  const apiSource = await readFile(new URL('../src/api/statistics.js', import.meta.url), 'utf8')

  assert.match(source, /@click="handleGenerate"/)
  assert.match(source, /generateReportApi/)
  assert.match(source, /window\.print\(\)/)
  assert.match(source, /@media print/)
  assert.doesNotMatch(source, /onMounted\([^)]*handleGenerate/)
  assert.match(dashboardSource, /buildReportRoute\(route\.path, dateRange\)/)
  assert.match(apiSource, /analysis\/reports[^\n]+timeout: 35000/)
})

test('AI report page loads history in a drawer without changing generation dates', async () => {
  const source = await readFile(new URL('../src/views/stats/Report.vue', import.meta.url), 'utf8')
  const apiSource = await readFile(new URL('../src/api/statistics.js', import.meta.url), 'utf8')

  assert.match(source, /历史报告/)
  assert.match(source, /<el-drawer/)
  assert.match(source, /historyDateRange/)
  assert.match(source, /fetchReportHistoryApi/)
  assert.match(source, /fetchReportDetailApi/)
  assert.match(source, /handleSelectHistory/)
  assert.match(source, /report\.value\s*=\s*response\.data\s*\|\|\s*response\s*\n\s*errorMessage\.value\s*=\s*''/)
  assert.match(source, />\s*生成新报告\s*</)
  assert.doesNotMatch(source, /dateRange\.value\s*=.*selectedReport/)
  assert.match(apiSource, /fetchReportHistory[^\n]+request\.get\('\/analysis\/reports'/)
  assert.match(apiSource, /fetchReportDetail[^\n]+request\.get\(`\/analysis\/reports\/\$\{id\}`\)/)
})

test('manual evidence uploads require and submit a supported violation type', async () => {
  const paths = [
    '../src/views/citizen/Report.vue',
    '../src/views/review/ImageUpload.vue',
    '../src/views/admin/ViolationUpload.vue'
  ]

  for (const path of paths) {
    const source = await readFile(new URL(path, import.meta.url), 'utf8')
    assert.match(source, /label="违法类型"[^>]*prop="reported_violation_type"/)
    assert.match(source, /value="illegal_stop"/)
    assert.match(source, /value="red_light_violation"/)
    assert.match(source, /reported_violation_type:\s*''/)
    assert.match(source, /reported_violation_type:\s*\[\{\s*required:\s*true/)
    assert.match(source, /fd\.append\('reported_violation_type',\s*form\.reported_violation_type\)/)
  }
})

test('case detail renders unique target labels and structured plate failures', async () => {
  const source = await readFile(new URL('../src/views/review/CaseDetail.vue', import.meta.url), 'utf8')

  assert.match(source, /v-for="\(obj, index\) in/)
  assert.match(source, /:key="obj\.detection_id \|\| `\$\{obj\.label\}-\$\{index\}`"/)
  assert.match(source, /obj\.display_label \|\| objLabel\(obj\.label\)/)
  assert.match(source, /detail\.plate_status_message/)
  assert.match(source, /主违法目标/)
  assert.match(source, /detail\.reported_violation_type/)
})
