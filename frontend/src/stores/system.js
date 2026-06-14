import { computed, reactive, ref } from 'vue'
import { defineStore } from 'pinia'
import api from '@/utils/api'

export const useSystemStore = defineStore('system', () => {
  const health = reactive({
    status: 'unknown',
    ganacheConnected: false,
    blockNumber: null,
    chainId: null,
    materialCount: 0,
    downloadCount: 0,
    ganacheUrl: '',
    deployer: '',
    contracts: {},
  })
  const loading = ref(false)
  const error = ref('')
  const lastCheckedAt = ref(null)
  let pollingTimer = null

  const connected = computed(
    () => health.status === 'running' && health.ganacheConnected,
  )

  async function refresh() {
    if (loading.value) return health
    loading.value = true
    try {
      const res = await api.get('/api/health')
      const data = res.data || {}
      health.status = data.status || 'unknown'
      health.ganacheConnected = Boolean(data.ganache_connected)
      health.blockNumber = data.block_number ?? null
      health.chainId = data.chain_id ?? null
      health.materialCount = Number(data.material_count || 0)
      health.downloadCount = Number(data.download_count || 0)
      health.ganacheUrl = data.ganache_url || ''
      health.deployer = data.deployer || ''
      health.contracts = data.contracts || {}
      error.value = ''
      lastCheckedAt.value = Date.now()
    } catch (requestError) {
      health.status = 'unavailable'
      health.ganacheConnected = false
      error.value = requestError.message || '系统状态获取失败'
      lastCheckedAt.value = Date.now()
    } finally {
      loading.value = false
    }
    return health
  }

  function startPolling(interval = 15000) {
    refresh()
    if (pollingTimer) window.clearInterval(pollingTimer)
    pollingTimer = window.setInterval(refresh, interval)
  }

  function stopPolling() {
    if (!pollingTimer) return
    window.clearInterval(pollingTimer)
    pollingTimer = null
  }

  return {
    health,
    loading,
    error,
    lastCheckedAt,
    connected,
    refresh,
    startPolling,
    stopPolling,
  }
})
