import test from 'node:test'
import assert from 'node:assert/strict'
import {
  buildApprovePayload,
  buildRejectPayload,
  buildViolationQuery,
  caseAiFallbackText,
  getCaseReviewOpinion,
  getStatisticsCards,
  isApprovedCaseStatus,
  mapNamedSeries,
  reportPathForRoute
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
