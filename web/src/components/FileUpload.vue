<script setup lang="ts">
import { ref } from 'vue'
import { Upload, FileText, CheckCircle, Loader2 } from 'lucide-vue-next'

defineProps<{
  uploading: boolean
  uploaded: boolean
  fileName: string
  error: string
}>()

const emit = defineEmits<{
  select: [file: File]
}>()

const dragOver = ref(false)

function handleDrop(e: DragEvent) {
  dragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) emit('select', file)
}

function handleChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) emit('select', file)
}
</script>

<template>
  <div>
    <div
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop="handleDrop"
      :class="[
        'relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200',
        uploaded ? 'border-green-300 bg-green-50' : dragOver ? 'border-indigo-400 bg-indigo-50' : 'border-gray-300 hover:border-indigo-300 hover:bg-gray-50',
        uploading && 'pointer-events-none opacity-60'
      ]"
    >
      <input
        type="file"
        accept=".pdf,.docx,.doc"
        @change="handleChange"
        class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        :disabled="uploading"
      />

      <!-- 上传中 -->
      <template v-if="uploading">
        <Loader2 class="w-10 h-10 mx-auto text-indigo-500 animate-spin" />
        <p class="mt-3 text-sm text-gray-500">正在上传...</p>
      </template>

      <!-- 已上传 -->
      <template v-else-if="uploaded">
        <CheckCircle class="w-10 h-10 mx-auto text-green-500" />
        <p class="mt-3 text-sm font-medium text-green-700">{{ fileName }}</p>
        <p class="text-xs text-green-500 mt-1">点击可重新上传</p>
      </template>

      <!-- 待上传 -->
      <template v-else>
        <Upload class="w-10 h-10 mx-auto text-gray-400" />
        <p class="mt-3 text-sm text-gray-600">点击或拖拽上传简历</p>
        <p class="text-xs text-gray-400 mt-1">支持 PDF / DOCX / DOC 格式</p>
      </template>
    </div>

    <!-- 错误提示 -->
    <p v-if="error" class="mt-2 text-sm text-red-500">{{ error }}</p>
  </div>
</template>
