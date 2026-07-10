/**
 * 图片接入 API — 连接真实后端
 */
import request from './request'

export const citizenReport = (formData) =>
  request.post('/intakes/citizen-reports', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

export const cameraCapture = (formData) =>
  request.post('/intakes/camera-captures', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

export const adminUpload = (formData) =>
  request.post('/intakes/admin-uploads', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
