/**
 * 公告管理 — 纯前端 localStorage 存储
 * 提供公告 CRUD 操作，管理员可发布/下架公告，首页展示已发布公告
 */

const STORAGE_KEY = 'app_announcements'

export interface Announcement {
  id: string
  title: string
  content: string
  is_published: boolean
  created_at: string
  updated_at: string
}

function getAll(): Announcement[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveAll(list: Announcement[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

/** 获得所有公告（管理员用） */
export function fetchAnnouncements(): Announcement[] {
  return getAll().sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}

/** 获得已发布的公告列表（首页用，最多5条） */
export function fetchPublished(): Announcement[] {
  return getAll()
    .filter(a => a.is_published)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)
}

/** 创建公告 */
export function createAnnouncement(data: Pick<Announcement, 'title' | 'content' | 'is_published'>): Announcement {
  const list = getAll()
  const now = new Date().toISOString().replace('T', ' ').slice(0, 19)
  const item: Announcement = {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    ...data,
    created_at: now,
    updated_at: now
  }
  list.push(item)
  saveAll(list)
  return item
}

/** 更新公告 */
export function updateAnnouncement(id: string, data: Partial<Pick<Announcement, 'title' | 'content' | 'is_published'>>): Announcement | null {
  const list = getAll()
  const idx = list.findIndex(a => a.id === id)
  if (idx === -1) return null
  list[idx] = {
    ...list[idx],
    ...data,
    updated_at: new Date().toISOString().replace('T', ' ').slice(0, 19)
  }
  saveAll(list)
  return list[idx]
}

/** 删除公告 */
export function deleteAnnouncement(id: string): boolean {
  const list = getAll()
  const filtered = list.filter(a => a.id !== id)
  if (filtered.length === list.length) return false
  saveAll(filtered)
  return true
}
