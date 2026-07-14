import request from './request'

export const fetchAnnouncements = params => request.get('/announcements', { params })
export const fetchAnnouncement = id => request.get(`/announcements/${id}`)
export const createAnnouncement = data => request.post('/admin/announcements', data)
export const updateAnnouncement = (id, data) => request.patch(`/admin/announcements/${id}`, data)
export const deleteAnnouncement = id => request.delete(`/admin/announcements/${id}`)
