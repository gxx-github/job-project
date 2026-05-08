<script setup lang="ts">
import { Download } from 'lucide-vue-next'
import { getDownloadUrl } from '../api/client'

defineProps<{
  type: string
  label: string
  icon: string
  description: string
}>()
</script>

<template>
  <div class="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
    <div class="text-center">
      <div class="text-4xl mb-3">{{ icon }}</div>
      <h3 class="text-lg font-semibold text-gray-900 mb-1">{{ label }}</h3>
      <p class="text-sm text-gray-500 mb-4">{{ description }}</p>
      <a
        :href="getDownloadUrl(type)"
        target="_blank"
        class="inline-flex items-center gap-2 px-5 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
      >
        <Download class="w-4 h-4" />
        下载文件
      </a>
    </div>
  </div>
</template>
