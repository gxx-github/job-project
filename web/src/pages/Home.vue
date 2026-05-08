<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Upload, FileText, Sparkles, Briefcase, Clock } from 'lucide-vue-next'
import { uploadResume } from '../api/client'
import { useSessionStore } from '../stores/session'
import FileUpload from '../components/FileUpload.vue'

const router = useRouter()
const store = useSessionStore()

const jobName = ref('Python开发工程师')
const jobAge = ref('3年')
const uploading = ref(false)
const uploaded = ref(false)
const errorMsg = ref('')

async function handleFileSelect(file: File) {
  uploading.value = true
  errorMsg.value = ''
  try {
    const result = await uploadResume(file)
    store.setSession(result.session_id, result.file_name)
    uploaded.value = true
  } catch (e: any) {
    errorMsg.value = e.message || '上传失败'
  } finally {
    uploading.value = false
  }
}

function handleStart() {
  if (!store.sessionId) {
    errorMsg.value = '请先上传简历'
    return
  }
  store.setJobParams(jobName.value, jobAge.value)
  router.push('/optimize')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-12">
    <div class="w-full max-w-lg">
      <!-- 标题 -->
      <div class="text-center mb-10">
        <div class="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 px-4 py-1.5 rounded-full text-sm font-medium mb-4">
          <Sparkles class="w-4 h-4" />
          AI 驱动
        </div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">AI 简历优化系统</h1>
        <p class="text-gray-500">上传简历，智能优化，一键生成面试准备材料</p>
      </div>

      <!-- 上传区域 -->
      <FileUpload
        :uploading="uploading"
        :uploaded="uploaded"
        :file-name="store.fileName"
        :error="errorMsg"
        @select="handleFileSelect"
      />

      <!-- 岗位信息 -->
      <div class="mt-8 space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">
            <Briefcase class="inline w-4 h-4 mr-1 -mt-0.5" />
            目标岗位
          </label>
          <input
            v-model="jobName"
            type="text"
            placeholder="例如: Python后端工程师"
            class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">
            <Clock class="inline w-4 h-4 mr-1 -mt-0.5" />
            工作年限
          </label>
          <input
            v-model="jobAge"
            type="text"
            placeholder="例如: 3年"
            class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
          />
        </div>
      </div>

      <!-- 提交按钮 -->
      <button
        @click="handleStart"
        :disabled="!uploaded"
        class="w-full mt-8 py-3 px-4 rounded-lg text-white font-medium transition-all duration-200"
        :class="uploaded
          ? 'bg-indigo-600 hover:bg-indigo-700 cursor-pointer shadow-lg shadow-indigo-200'
          : 'bg-gray-300 cursor-not-allowed'"
      >
        <Sparkles class="inline w-5 h-5 mr-2 -mt-0.5" />
        开始优化
      </button>
    </div>
  </div>
</template>
