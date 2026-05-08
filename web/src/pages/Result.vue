<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import ResultCard from '../components/ResultCard.vue'
import { ArrowLeft, Sparkles } from 'lucide-vue-next'

const router = useRouter()
const store = useSessionStore()

const files = [
  { type: 'pdf',        label: '优化简历 PDF',   icon: '📄', description: '排版精美的 PDF 格式简历' },
  { type: 'markdown',   label: 'Markdown 版本',   icon: '📝', description: 'Markdown 格式，方便二次编辑' },
  { type: 'self_intro', label: '自我介绍',         icon: '🎤', description: '针对岗位定制的自我介绍' },
  { type: 'interview',  label: '面试题集锦',       icon: '💼', description: '基于简历生成的面试问答' },
  { type: 'summary',    label: '优化总结',         icon: '📊', description: '本次优化改动摘要' },
]
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-12 px-4">
    <div class="max-w-3xl mx-auto">
      <!-- 标题 -->
      <div class="text-center mb-10">
        <div class="inline-flex items-center gap-2 bg-green-50 text-green-700 px-4 py-1.5 rounded-full text-sm font-medium mb-4">
          <Sparkles class="w-4 h-4" />
          优化完成
        </div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">简历优化结果</h1>
        <p class="text-gray-500">所有文件已生成，点击下方卡片下载</p>
      </div>

      <!-- 文件卡片 -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <ResultCard
          v-for="file in files"
          :key="file.type"
          :type="file.type"
          :label="file.label"
          :icon="file.icon"
          :description="file.description"
        />
      </div>

      <!-- 返回按钮 -->
      <div class="text-center mt-10">
        <button
          @click="store.reset(); router.push('/')"
          class="inline-flex items-center gap-2 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft class="w-4 h-4" />
          重新优化
        </button>
      </div>
    </div>
  </div>
</template>
