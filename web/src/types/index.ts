export interface UploadResult {
  session_id: string
  file_name: string
  file_size: number
}

export interface AgentStep {
  name: string
  label: string
  status: 'pending' | 'running' | 'done' | 'error' | 'cached'
  content?: string
}

export interface OptimizeParams {
  job_name: string
  job_age: string
}

// WebSocket 消息类型
export type WSMessage =
  | { type: 'status'; message: string }
  | { type: 'agent_start'; agent: string }
  | { type: 'agent_done'; agent: string; current: number; total: number; content: string }
  | { type: 'memory_hit'; agent: string }
  | { type: 'progress'; agent: string; message: string }
  | { type: 'complete'; outputs: OutputFiles; sections: Record<string, string>; memory_hits: string[] }
  | { type: 'error'; message: string }

export interface OutputFiles {
  pdf: string
  markdown: string
  self_intro: string
  interview: string
  summary: string
}

export interface MemoryEntry {
  file: string
  section_key: string
  hash: string
  context: Record<string, string>
}

export const AGENT_LIST: AgentStep[] = [
  { name: 'extractor',          label: '简历提取',     status: 'pending' },
  { name: 'title',              label: '标题优化',     status: 'pending' },
  { name: 'personal_info',      label: '个人信息',     status: 'pending' },
  { name: 'skills',             label: '专业技能',     status: 'pending' },
  { name: 'certificate',        label: '技能证书',     status: 'pending' },
  { name: 'work_experience',    label: '职业经历',     status: 'pending' },
  { name: 'education',          label: '教育经历',     status: 'pending' },
  { name: 'project_experience', label: '项目经验',     status: 'pending' },
  { name: 'self_evaluation',    label: '自我评价',     status: 'pending' },
  { name: 'assembler',          label: '简历组装',     status: 'pending' },
  { name: 'layout_expert',      label: '排版渲染',     status: 'pending' },
  { name: 'interviewer',        label: '面试准备',     status: 'pending' },
]
