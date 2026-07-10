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

function normalizeOptionalText(value) {
  if (value == null) return null
  const normalized = String(value).trim()
  return normalized || null
}

export function buildVehicleQuery(filters = {}, page = 1, pageSize = 10) {
  const query = { page, page_size: pageSize }
  const plateNo = normalizeOptionalText(filters.plate)

  if (plateNo) query.plate_no = plateNo
  return query
}

export function buildVehiclePayload(form = {}) {
  return {
    plate_no: normalizeOptionalText(form.plate_no),
    owner_id: form.owner_id === '' || form.owner_id == null ? null : form.owner_id,
    vehicle_type: normalizeOptionalText(form.vehicle_type),
    color: normalizeOptionalText(form.color)
  }
}

export function buildUserCreatePayload(form = {}) {
  return {
    username: normalizeOptionalText(form.username),
    password: form.password,
    phone: normalizeOptionalText(form.phone),
    email: normalizeOptionalText(form.email),
    role_code: normalizeOptionalText(form.role_code)
  }
}

export function buildUserUpdatePayload(form = {}) {
  const payload = {}

  for (const field of ['phone', 'email', 'role_code', 'status']) {
    if (form[field] !== undefined) payload[field] = normalizeOptionalText(form[field])
  }
  if (typeof form.password === 'string' && form.password.trim()) {
    payload.password = form.password
  }

  return payload
}

export async function persistUserStatus(row, newStatus, persist) {
  try {
    await persist(row.id, { status: newStatus })
    return true
  } catch {
    row.status = newStatus === 'active' ? 'disabled' : 'active'
    return false
  }
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

export function summarizeCitizenOverview(violations = {}, cases = {}, vehicles = {}) {
  return {
    violations: violations.total ?? 0,
    reports: cases.total ?? 0,
    rewards: (cases.items ?? []).reduce((total, item) => total + (item?.reward ?? 0), 0),
    vehicles: vehicles.total ?? 0
  }
}

export async function fetchAllCitizenCases(fetchPage, pageSize = 100) {
  const firstPage = await fetchPage({ source_type: 'citizen', page: 1, page_size: pageSize })
  const totalPages = Math.ceil((firstPage.total ?? 0) / (firstPage.page_size ?? pageSize))
  const remainingPages = await Promise.all(
    Array.from({ length: Math.max(0, totalPages - 1) }, (_, index) =>
      fetchPage({ source_type: 'citizen', page: index + 2, page_size: pageSize })
    )
  )

  return {
    ...firstPage,
    items: [firstPage, ...remainingPages].flatMap(page => page.items ?? [])
  }
}
