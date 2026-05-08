import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSessionStore = defineStore('session', () => {
  const sessionId = ref('')
  const fileName = ref('')
  const jobName = ref('')
  const jobAge = ref('')

  function setSession(id: string, name: string) {
    sessionId.value = id
    fileName.value = name
  }

  function setJobParams(name: string, age: string) {
    jobName.value = name
    jobAge.value = age
  }

  function reset() {
    sessionId.value = ''
    fileName.value = ''
    jobName.value = ''
    jobAge.value = ''
  }

  return { sessionId, fileName, jobName, jobAge, setSession, setJobParams, reset }
})
