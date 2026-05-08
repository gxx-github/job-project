import type { UploadResult, MemoryEntry } from '../types'

const API_BASE = '/api'

export async function uploadResume(file: File): Promise<UploadResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '上传失败' }))
    throw new Error(err.detail || '上传失败')
  }
  return res.json()
}

export async function listTechStacks(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/tech-stacks`)
  const data = await res.json()
  return data.tech_stacks
}

export function getDownloadUrl(type: string): string {
  return `${API_BASE}/download/${type}`
}

export async function listMemory(): Promise<{ entries: MemoryEntry[]; total: number }> {
  const res = await fetch(`${API_BASE}/memory`)
  return res.json()
}

export async function clearMemory(sectionKey: string): Promise<void> {
  await fetch(`${API_BASE}/memory/${sectionKey}`, { method: 'DELETE' })
}
