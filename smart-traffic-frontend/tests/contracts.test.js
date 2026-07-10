import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import * as contracts from '../src/utils/contracts.js'
import {
  buildApprovePayload,
  buildRejectPayload,
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

test('describes missing AI results according to case processing state', () => {
  assert.equal(caseAiFallbackText('detecting'), 'AI 处理中...')
  assert.equal(caseAiFallbackText('ai_reviewing'), 'AI 处理中...')

  for (const status of ['uploaded', 'pending_human_review', 'approved', 'rejected', 'notified']) {
    assert.equal(caseAiFallbackText(status), '暂无 AI 结果')
  }
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
