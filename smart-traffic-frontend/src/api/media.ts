import request from './request'
import { mediaPathToApiPath } from '@/utils/contracts'

export async function fetchProtectedMediaUrl(mediaUrl) {
  const response = await request.get(mediaPathToApiPath(mediaUrl), {
    responseType: 'blob'
  })
  return URL.createObjectURL(response.data)
}
