export function getStatisticsCards(data = {}) {
  return [
    { label: '总案件数', value: data.total_cases ?? 0, color: '#409eff' },
    { label: '违章记录数', value: data.total_violations ?? 0, color: '#67c23a' },
    { label: '通过率', value: `${data.approve_rate ?? 0}%`, color: '#409eff' },
    { label: '驳回率', value: `${data.reject_rate ?? 0}%`, color: '#f56c6c' },
    { label: '待审核', value: data.pending_count ?? 0, color: '#e6a23c' },
    { label: '今日新增', value: data.today_new ?? 0, color: '#909399' }
  ]
}

export function mapNamedSeries(data = {}) {
  return (data.items ?? []).map(({ name, value }) => ({ name, value }))
}

export function buildViolationQuery(filters = {}, page = 1, pageSize = 10) {
  const query = { page, page_size: pageSize }

  if (filters.plate) query.plate_no = filters.plate
  if (filters.type) query.violation_type = filters.type
  if (filters.location) query.location_text = filters.location
  if (filters.status) query.status = filters.status
  if (filters.dateRange?.length === 2) {
    query.start_time = `${filters.dateRange[0]}T00:00:00`
    query.end_time = `${filters.dateRange[1]}T23:59:59`
  }

  return query
}

export function buildApprovePayload(form) {
  return {
    plate_no: form.plate_no,
    violation_type: form.violation_type,
    fine_amount: form.fine_amount,
    points: form.points,
    review_opinion: form.review_opinion
  }
}

export function buildRejectPayload(form) {
  return { reject_reason: form.review_opinion }
}

export function reportPathForRoute(path) {
  return path.startsWith('/admin/') ? '/admin/stats/report' : '/stats/report'
}

export function caseAiFallbackText(status) {
  return ['detecting', 'ai_reviewing'].includes(status) ? 'AI 处理中...' : '暂无 AI 结果'
}

export function isApprovedCaseStatus(status) {
  return ['approved', 'notified'].includes(status)
}

export function getCaseReviewOpinion(detail = {}) {
  return detail.review?.review_opinion ?? ''
}
