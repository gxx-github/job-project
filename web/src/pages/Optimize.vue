<script setup lang="ts">
import { onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWebSocket } from '../composables/useWebSocket'
import { useSessionStore } from '../stores/session'
import { AGENT_LIST } from '../types'
import AgentPipeline from '../components/AgentPipeline.vue'
import { Briefcase, Clock, CircleAlert, Loader2 } from 'lucide-vue-next'

const router = useRouter()
const store = useSessionStore()
const { messages, status, connect } = useWebSocket()

// 如果没有 session，跳回首页
onMounted(() => {
  if (!store.sessionId) {
    router.replace('/')
    return
  }
  connect(store.sessionId, { job_name: store.jobName, job_age: store.jobAge })
})

// 完成后跳转结果页
watch(status, (val) => {
  if (val === 'done') {
    setTimeout(() => router.push('/result'), 800)
  }
})

const doneCount = computed(() => {
  let count = 0
  for (const msg of messages.value) {
    if (msg.type === 'agent_done') count++
  }
  return count
})

const progressPercent = computed(() => {
  return Math.round((doneCount.value / AGENT_LIST.length) * 100)
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-12 px-4">
    <div class="max-w-2xl mx-auto">
      <!-- 头部信息 -->
      <div class="text-center mb-8">
        <h2 class="text-2xl font-bold text-gray-900 mb-2">正在优化简历...</h2>
        <div class="flex items-center justify-center gap-4 text-sm text-gray-500">
          <span class="flex items-center gap-1">
            <Briefcase class="w-4 h-4" />
            {{ store.jobName }}
          </span>
          <span class="flex items-center gap-1">
            <Clock class="w-4 h-4" />
            {{ store.jobAge }}
          </span>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="mb-8">
        <div class="flex justify-between text-sm text-gray-500 mb-1">
          <span>{{ doneCount }} / {{ AGENT_LIST.length }} 个步骤</span>
          <span>{{ progressPercent }}%</span>
        </div>
        <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            class="h-full bg-indigo-600 rounded-full transition-all duration-500"
            :style="{ width: `${progressPercent}%` }"
          />
        </div>
      </div>

      <!-- Agent Pipeline -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <AgentPipeline :messages="messages" />
      </div>

      <!-- 错误状态 -->
      <div
        v-if="status === 'error'"
        class="mt-6 bg-red-50 border border-red-200 rounded-xl p-6 text-center"
      >
        <CircleAlert class="w-8 h-8 mx-auto text-red-500 mb-2" />
        <p class="text-red-700 font-medium">执行出错</p>
        <p class="text-sm text-red-500 mt-1">
          {{ messages.find(m => m.type === 'error')?.message || '请重试' }}
        </p>
        <button
          @click="router.push('/')"
          class="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
        >
          返回首页
        </button>
      </div>
    </div>
  </div>
</template>
