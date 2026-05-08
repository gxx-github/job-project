<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle, Loader2, Clock, Zap, CircleAlert } from 'lucide-vue-next'
import type { WSMessage } from '../types'
import { AGENT_LIST } from '../types'

const props = defineProps<{
  messages: WSMessage[]
}>()

const agentStatusMap = computed(() => {
  const map: Record<string, 'done' | 'cached' | 'running' | 'error'> = {}
  const runningSet = new Set<string>()

  for (const msg of props.messages) {
    if (msg.type === 'agent_done') {
      runningSet.delete(msg.agent)
      map[msg.agent] = 'done'
    }
    if (msg.type === 'memory_hit') {
      map[msg.agent] = 'cached'
    }
    if (msg.type === 'agent_start') {
      runningSet.add(msg.agent)
    }
    if (msg.type === 'error') {
      runningSet.clear()
    }
  }
  // Mark still-running agents
  for (const agent of runningSet) {
    if (!map[agent]) map[agent] = 'running'
  }
  return map
})

const currentAgent = computed(() => {
  const doneCount = Object.keys(agentStatusMap.value).length
  // Find first pending agent as current
  for (const agent of AGENT_LIST) {
    if (!agentStatusMap.value[agent.name]) return agent.name
  }
  return ''
})

const lastProgress = computed(() => {
  for (let i = props.messages.length - 1; i >= 0; i--) {
    const msg = props.messages[i]
    if (msg.type === 'progress' || msg.type === 'status') return msg.message
  }
  return ''
})

function getStatus(name: string): string {
  if (name === currentAgent.value && !agentStatusMap.value[name]) return 'running'
  return agentStatusMap.value[name] || 'pending'
}
</script>

<template>
  <div class="space-y-1">
    <div
      v-for="agent in AGENT_LIST"
      :key="agent.name"
      :class="[
        'flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-300',
        getStatus(agent.name) === 'running' && 'bg-indigo-50',
        getStatus(agent.name) === 'done' && 'bg-green-50',
        getStatus(agent.name) === 'cached' && 'bg-blue-50',
        getStatus(agent.name) === 'pending' && 'opacity-50'
      ]"
    >
      <!-- 图标 -->
      <div class="flex-shrink-0">
        <CheckCircle v-if="getStatus(agent.name) === 'done'" class="w-5 h-5 text-green-500" />
        <Zap v-else-if="getStatus(agent.name) === 'cached'" class="w-5 h-5 text-blue-500" />
        <Loader2 v-else-if="getStatus(agent.name) === 'running'" class="w-5 h-5 text-indigo-500 animate-spin" />
        <CircleAlert v-else-if="getStatus(agent.name) === 'error'" class="w-5 h-5 text-red-500" />
        <Clock v-else class="w-5 h-5 text-gray-400" />
      </div>

      <!-- 标签 -->
      <span
        :class="[
          'text-sm font-medium',
          getStatus(agent.name) === 'done' && 'text-green-700',
          getStatus(agent.name) === 'cached' && 'text-blue-700',
          getStatus(agent.name) === 'running' && 'text-indigo-700',
          getStatus(agent.name) === 'pending' && 'text-gray-500'
        ]"
      >
        {{ agent.label }}
      </span>

      <!-- 缓存标签 -->
      <span
        v-if="getStatus(agent.name) === 'cached'"
        class="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full"
      >
        缓存命中
      </span>
    </div>

    <!-- 进度信息 -->
    <p v-if="lastProgress" class="text-sm text-gray-500 mt-4 px-4">
      {{ lastProgress }}
    </p>
  </div>
</template>
