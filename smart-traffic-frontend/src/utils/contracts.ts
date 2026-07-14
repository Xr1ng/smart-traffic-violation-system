import type { ApiResponse, PaginatedData } from '@/types'
import type { StatisticsOverview } from '@/types'

// ─── 大屏统计 ────────────────────────────────────────

export interface StatCard {
  label: string
  value: string | number
  color: string
}

export function getStatisticsCards(data: Partial<StatisticsOverview> = {}): StatCard[] {
  return [
    { label: '总案件数', value: data.total_cases ?? 0, color: '#72a8c4' },
    { label: '违章记录数', value: data.total_violations ?? 0, color: '#67c23a' },
    { label: '通过率', value: `${data.approve_rate ?? 0}%`, color: '#72a8c4' },
    { label: '驳回率', value: `${data.reject_rate ?? 0}%`, color: '#f56c6c' },
    { label: '待审核', value: data.pending_count ?? 0, color: '#e6a23c' },
    { label: '今日新增', value: data.today_new ?? 0, color: '#909399' },
  ]
}

export interface NamedValue {
  name: string
  value: number
}

export function mapNamedSeries(data: { items?: NamedValue[] } = {}): NamedValue[] {
  return (data.items ?? []).map(({ name, value }) => ({ name, value }))
}

// ─── 违章查询 ────────────────────────────────────────

export interface ViolationFilters {
  plate?: string
  type?: string
  location?: string
  status?: string
  dateRange?: [string, string]
}

export interface ViolationQueryParams {
  page: number
  page_size: number
  plate_no?: string
  violation_type?: string
  location_text?: string
  status?: string
  start_time?: string
  end_time?: string
}

export function buildViolationQuery(
  filters: ViolationFilters = {},
  page = 1,
  pageSize = 10,
): ViolationQueryParams {
  const query: ViolationQueryParams = { page, page_size: pageSize }

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

// ─── 车辆管理 ────────────────────────────────────────

export interface VehicleFilters {
  plate?: string
}

export interface VehicleQueryParams {
  page: number
  page_size: number
  plate_no?: string
}

function normalizeOptionalText(value: unknown): string | null {
  if (value == null) return null
  const normalized = String(value).trim()
  return normalized || null
}

export function buildVehicleQuery(
  filters: VehicleFilters = {},
  page = 1,
  pageSize = 10,
): VehicleQueryParams {
  const query: VehicleQueryParams = { page, page_size: pageSize }
  const plateNo = normalizeOptionalText(filters.plate)
  if (plateNo) query.plate_no = plateNo
  return query
}

export interface VehicleFormData {
  plate_no?: string
  owner_id?: number | null | ''
  vehicle_type?: string | null
  color?: string | null
}

export interface VehicleCreatePayload {
  plate_no: string | null
  owner_id: number | null
  vehicle_type: string | null
  color: string | null
}

export function buildVehiclePayload(form: VehicleFormData = {}): VehicleCreatePayload {
  return {
    plate_no: normalizeOptionalText(form.plate_no),
    owner_id: form.owner_id === '' || form.owner_id == null ? null : form.owner_id as number,
    vehicle_type: normalizeOptionalText(form.vehicle_type),
    color: normalizeOptionalText(form.color),
  }
}

// ─── 用户管理 ────────────────────────────────────────

export interface UserFormData {
  username?: string
  password?: string
  phone?: string
  email?: string
  role_code?: string
  status?: string
}

export interface UserCreatePayload {
  username: string | null
  password: string | undefined
  phone: string | null
  email: string | null
  role_code: string | null
}

export function buildUserCreatePayload(form: UserFormData = {}): UserCreatePayload {
  return {
    username: normalizeOptionalText(form.username),
    password: form.password,
    phone: normalizeOptionalText(form.phone),
    email: normalizeOptionalText(form.email),
    role_code: normalizeOptionalText(form.role_code),
  }
}

export function buildUserUpdatePayload(form: UserFormData = {}): Record<string, unknown> {
  const payload: Record<string, unknown> = {}
  for (const field of ['phone', 'email', 'role_code', 'status'] as const) {
    if (form[field] !== undefined) payload[field] = normalizeOptionalText(form[field])
  }
  if (typeof form.password === 'string' && form.password.trim()) {
    payload.password = form.password
  }
  return payload
}

export async function persistUserStatus(
  row: { id: number; status: string },
  newStatus: string,
  persist: (id: number, data: Record<string, unknown>) => Promise<unknown>,
): Promise<boolean> {
  try {
    await persist(row.id, { status: newStatus })
    return true
  } catch {
    row.status = newStatus === 'active' ? 'disabled' : 'active'
    return false
  }
}

// ─── 审核操作 ────────────────────────────────────────

export interface ReviewFormData {
  plate_no: string
  violation_type: string
  fine_amount: number
  points: number
  review_opinion: string
}

export function buildApprovePayload(form: ReviewFormData) {
  return {
    plate_no: form.plate_no,
    violation_type: form.violation_type,
    fine_amount: form.fine_amount,
    points: form.points,
    review_opinion: form.review_opinion,
  }
}

export function buildRejectPayload(form: { review_opinion: string }) {
  return { reject_reason: form.review_opinion }
}

// ─── 报告路由 ────────────────────────────────────────

export function reportPathForRoute(path: string): string {
  return path.startsWith('/admin/') ? '/admin/stats/report' : '/stats/report'
}

export interface ReportRequest {
  start_time: string
  end_time: string
}

export function buildReportRequest(dateRange: [string | Date, string | Date]): ReportRequest {
  if (!Array.isArray(dateRange) || dateRange.length !== 2) {
    throw new TypeError('报告日期范围必须包含开始和结束日期')
  }
  const start = new Date(dateRange[0])
  const end = new Date(dateRange[1])
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    throw new TypeError('报告日期范围无效')
  }
  start.setHours(0, 0, 0, 0)
  end.setHours(23, 59, 59, 999)
  return { start_time: start.toISOString(), end_time: end.toISOString() }
}

export function buildReportRoute(path: string, dateRange: [string | Date, string | Date]) {
  return {
    path: reportPathForRoute(path),
    query: buildReportRequest(dateRange),
  }
}

// ─── 案件工具 ────────────────────────────────────────

export function caseAiFallbackText(status: string): string {
  return ['detecting', 'ai_reviewing'].includes(status) ? 'AI 处理中...' : '暂无 AI 结果'
}

export function mediaPathToApiPath(mediaUrl: string): string {
  const match = /^\/media\/([^/?#]+)$/.exec(mediaUrl ?? '')
  if (!match) throw new Error('Unsupported media URL')
  return `/media/${encodeURIComponent(decodeURIComponent(match[1]))}`
}

export async function loadProtectedMediaUrls(
  media: Record<string, string | null> = {},
  loadMedia: (url: string) => Promise<string>,
): Promise<Record<string, string | null>> {
  const entries = await Promise.all(
    Object.entries(media).map(async ([key, url]) => {
      if (!url) return [key, null] as const
      try {
        return [key, await loadMedia(url)] as const
      } catch {
        return [key, null] as const
      }
    }),
  )
  return Object.fromEntries(entries)
}

export function releaseProtectedMediaUrls(
  media: Record<string, unknown> = {},
  revoke: (url: string) => void = URL.revokeObjectURL,
): void {
  for (const url of Object.values(media)) {
    if (typeof url === 'string' && url.startsWith('blob:')) revoke(url)
  }
}

// ─── 竞态请求守卫 ─────────────────────────────────────

export interface LatestRequestGuard {
  begin(): number
  isCurrent(generation: number): boolean
  invalidate(): void
}

export function createLatestRequestGuard(): LatestRequestGuard {
  let generation = 0
  let active = true

  return {
    begin() {
      generation += 1
      return generation
    },
    isCurrent(requestGeneration) {
      return active && requestGeneration === generation
    },
    invalidate() {
      active = false
      generation += 1
    }
  }
}

// ─── 案件状态 ────────────────────────────────────────

export function isApprovedCaseStatus(status: string): boolean {
  return ['approved', 'notified'].includes(status)
}

export function getCaseReviewOpinion(detail: { review?: { review_opinion?: string } } = {}): string {
  return detail.review?.review_opinion ?? ''
}

// ─── 市民概览 ────────────────────────────────────────

export interface CitizenOverview {
  violations: number
  reports: number
  rewards: number
  vehicles: number
}

export function summarizeCitizenOverview(
  violations: { total?: number } = {},
  cases: { total?: number; items?: Array<{ reward?: number }> } = {},
  vehicles: { total?: number } = {},
): CitizenOverview {
  return {
    violations: violations.total ?? 0,
    reports: cases.total ?? 0,
    rewards: (cases.items ?? []).reduce((total, item) => total + (item?.reward ?? 0), 0),
    vehicles: vehicles.total ?? 0,
  }
}

// ─── 全量分页获取 ────────────────────────────────────

export async function fetchAllCitizenCases<T extends { total?: number; page_size?: number; items?: unknown[] }>(
  fetchPage: (params: { source_type: string; page: number; page_size: number }) => Promise<T>,
  pageSize = 100,
): Promise<T & { items: unknown[] }> {
  const firstPage = await fetchPage({ source_type: 'citizen', page: 1, page_size: pageSize })
  const totalPages = Math.ceil((firstPage.total ?? 0) / (firstPage.page_size ?? pageSize))
  const remainingPages = await Promise.all(
    Array.from({ length: Math.max(0, totalPages - 1) }, (_, index) =>
      fetchPage({ source_type: 'citizen', page: index + 2, page_size: pageSize }),
    ),
  )

  return {
    ...firstPage,
    items: [firstPage, ...remainingPages].flatMap(page => page.items ?? []),
  }
}
