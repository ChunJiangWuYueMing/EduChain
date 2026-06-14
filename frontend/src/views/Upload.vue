<template>
  <main class="upload-page">
    <section class="upload-content">
      <div class="upload-main">
        <section class="hero-card">
          <div>
            <h2>上传资料</h2>
            <p>上传文件并完成链上存证</p>
          </div>
        </section>

        <section class="form-card">
          <label
            class="drop-zone"
            :class="{ dragging: isDragging, filled: selectedFile }"
            @dragenter.prevent="isDragging = true"
            @dragover.prevent
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
          >
            <input ref="fileInput" type="file" :accept="acceptedTypes" hidden @change="handleFileChange" />
            <span class="upload-icon">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 3v12" />
                <path d="m7 8 5-5 5 5" />
                <path d="M5 15a4 4 0 0 0 0 8h14a4 4 0 0 0 0-8" />
              </svg>
            </span>
            <strong>{{ selectedFile ? selectedFile.name : '拖拽文件到此处或点击选择文件' }}</strong>
            <p>{{ selectedFile ? formatSize(selectedFile.size) : '支持 pdf、docx、pptx、txt、md，不超过 50MB' }}</p>
            <button type="button" class="select-button" @click.prevent="fileInput?.click()">选择文件</button>
          </label>

          <label class="field">
            <span>课程编号</span>
            <select v-model="form.course">
              <option value="">选择课程或输入课程编号</option>
              <option v-for="course in courseCatalog" :key="course.code" :value="course.code">
                {{ course.code }} {{ course.name }}
              </option>
            </select>
          </label>

          <label class="field">
            <span>下载价格（EDU）</span>
            <div class="number-shell">
              <input v-model.number="form.price" type="number" min="0" max="999" />
              <span>EDU</span>
            </div>
          </label>

          <fieldset class="policy-group">
            <legend>访问策略</legend>
            <label>
              <input v-model="form.policy" type="radio" value="public" />
              <span>公开</span>
              <em>任何人可见并下载</em>
            </label>
            <label>
              <input v-model="form.policy" type="radio" value="same-course" />
              <span>同课程</span>
              <em>仅本课程学生可见</em>
            </label>
            <label>
              <input v-model="form.policy" type="radio" value="whitelist" />
              <span>指定用户</span>
              <em>仅白名单地址可下载</em>
            </label>
          </fieldset>

          <label v-if="form.policy === 'whitelist'" class="field whitelist-field">
            <span>白名单地址</span>
            <textarea
              v-model.trim="form.policyValue"
              rows="3"
              placeholder="输入 0x 开头的钱包地址，多个地址请用逗号或换行分隔"
            ></textarea>
            <small :class="{ invalid: form.policyValue && !whitelistValid }">
              {{ whitelistHint }}
            </small>
          </label>

          <button type="button" class="submit-button" :disabled="!canSubmit || loading" @click="handleUpload">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3v12" />
              <path d="m7 8 5-5 5 5" />
              <path d="M5 15v4h14v-4" />
            </svg>
            {{ loading ? '上传并存证中...' : '上传并存证' }}
          </button>
        </section>

        <section class="progress-card">
          <h2>上传进度</h2>
          <div class="steps">
            <div v-for="step in steps" :key="step.title" class="step" :class="{ active: step.index === currentStep, done: step.index < currentStep }">
              <span>{{ step.index }}</span>
              <strong>{{ step.title }}</strong>
              <p>{{ step.desc }}</p>
            </div>
          </div>
        </section>
      </div>

      <aside class="result-panel">
        <section class="result-card">
          <h2>上传结果</h2>

          <div v-if="result" class="success-banner">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m8 12 3 3 5-6" />
              <circle cx="12" cy="12" r="9" />
            </svg>
            <div>
              <strong>上传成功，已完成链上存证</strong>
              <p>文件已安全存证至区块链</p>
            </div>
          </div>

          <div v-else class="pending-banner">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3v12" />
              <path d="m7 8 5-5 5 5" />
              <path d="M5 15a4 4 0 0 0 0 8h14a4 4 0 0 0 0-8" />
            </svg>
            <div>
              <strong>等待上传</strong>
              <p>选择文件并提交后，将展示链上存证结果</p>
            </div>
          </div>

          <dl class="result-list">
            <div v-for="row in resultRows" :key="row.label">
              <dt>{{ row.label }}</dt>
              <dd>
                {{ row.value }}
                <button
                  v-if="row.copy"
                  type="button"
                  :aria-label="`复制${row.label}`"
                  @click="copyValue(row.value, row.label)"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <rect x="9" y="9" width="11" height="11" rx="2" />
                    <rect x="4" y="4" width="11" height="11" rx="2" />
                  </svg>
                </button>
              </dd>
            </div>
          </dl>
        </section>

        <section class="similar-card">
          <h2>相似资料 <span>（基于 SimHash）</span></h2>
          <table v-if="result">
            <thead>
              <tr>
                <th>资料 ID</th>
                <th>资料名称</th>
                <th>课程</th>
                <th>相似度 / 汉明距离</th>
                <th>分类</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in similarMaterials" :key="item.id">
                <td>{{ item.id }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.course }}</td>
                <td>{{ item.score }} / {{ item.distance }}</td>
                <td><span class="similar-tag" :class="item.type">{{ item.label }}</span></td>
              </tr>
              <tr v-if="similarMaterials.length === 0">
                <td colspan="5" class="similar-empty-row">未发现需要提示的相似资料</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="similar-empty">上传完成后会自动比对相似资料。</div>
        </section>

        <section class="notice-card">
          <div>
            <strong>上传须知</strong>
            <p>请确保您拥有资料的合法版权或授权，上传的资料需遵守学校相关规定与法律法规。</p>
          </div>
          <button type="button" @click="rulesOpen = true">查看上传规则</button>
        </section>

        <div class="panel-actions">
          <button type="button" class="secondary-action" @click="router.push('/market')">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5" /><path d="m12 19-7-7 7-7" /></svg>
            返回市场
          </button>
          <button type="button" class="primary-action" :disabled="!result" @click="resetForm">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12" /><path d="m7 8 5-5 5 5" /><path d="M5 15v4h14v-4" /></svg>
            {{ result ? '继续上传' : '等待上传' }}
          </button>
        </div>
      </aside>
    </section>

    <Teleport to="body">
      <div v-if="rulesOpen" class="rules-backdrop" @click.self="rulesOpen = false">
        <section class="rules-dialog" role="dialog" aria-modal="true" aria-labelledby="upload-rules-title">
          <header>
            <h2 id="upload-rules-title">资料上传规则</h2>
            <button type="button" aria-label="关闭上传规则" @click="rulesOpen = false">×</button>
          </header>
          <ol>
            <li>仅上传拥有版权、已获授权或允许用于课程交流的资料。</li>
            <li>文件不得包含违法内容、恶意代码、他人隐私或未脱敏的敏感信息。</li>
            <li>课程编号、价格和访问策略应与资料用途一致，链上登记后会形成可审计记录。</li>
            <li>白名单策略仅接受有效的以太坊地址，多个地址可使用逗号或换行分隔。</li>
            <li>系统会计算 SHA-256 与 SimHash；发现高相似资料时，请确认不存在重复提交。</li>
          </ol>
          <button type="button" class="primary-action" @click="rulesOpen = false">我已了解</button>
        </section>
      </div>
    </Teleport>

    <div v-if="toast" class="toast" role="status">{{ toast }}</div>
  </main>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { formatTime } from '@/utils/api'
import { useAuthStore } from '@/stores/auth'
import { copyText } from '@/utils/clipboard'
import { courseCatalog, courseDisplay } from '@/config/courses'

const router = useRouter()
const auth = useAuthStore()
const fileInput = ref(null)
const selectedFile = ref(null)
const isDragging = ref(false)
const loading = ref(false)
const result = ref(null)
const toast = ref('')
const rulesOpen = ref(false)
const acceptedTypes = '.pdf,.docx,.pptx,.txt,.md'

const form = reactive({
  course: '',
  price: 12,
  policy: 'public',
  policyValue: '',
})

const steps = [
  { index: 1, title: '文件指纹计算中', desc: '计算文件哈希与指纹' },
  { index: 2, title: '链上登记中', desc: '将元数据写入区块链' },
  { index: 3, title: '上传奖励确认中', desc: '确认并发放上传奖励' },
]

const similarMaterials = computed(() => (result.value?.similar_materials || []).map((item) => ({
  id: item.material_id || item.id || '--',
  name: item.material_name || item.name || '链上相似资料',
  course: courseDisplay(item.course),
  score: item.similarity_percent ?? item.similarity ?? item.similarity_pct ?? '--',
  distance: item.hamming_distance ?? item.distance ?? '--',
  type: item.classification || 'derived',
  label: {
    identical: '完全相同',
    high: '高度相似',
    derived: '衍生资料',
    different: '差异较大',
  }[item.classification] || '相似资料',
})))

const whitelistAddresses = computed(() => form.policyValue
  .split(/[\n,]/)
  .map((value) => value.trim())
  .filter(Boolean))
const whitelistValid = computed(() => (
  whitelistAddresses.value.length > 0
  && whitelistAddresses.value.every((value) => /^0x[a-fA-F0-9]{40}$/.test(value))
))
const whitelistHint = computed(() => {
  if (!form.policyValue) return '至少填写一个钱包地址'
  if (!whitelistValid.value) return '存在格式无效的地址，请检查 0x 地址长度'
  return `已识别 ${whitelistAddresses.value.length} 个有效地址`
})
const canSubmit = computed(() => (
  selectedFile.value
  && form.course
  && form.price >= 0
  && (form.policy !== 'whitelist' || whitelistValid.value)
))
const currentStep = computed(() => {
  if (result.value) return 4
  if (loading.value) return 2
  if (selectedFile.value) return 1
  return 0
})
const resultRows = computed(() => {
  const data = result.value
  return [
    { label: '资料 ID', value: data?.material_id || '--', copy: !!data },
    { label: '资料名称', value: data?.name || '--', copy: !!data },
    { label: 'SHA-256', value: data?.sha256_hash || '--', copy: !!data },
    { label: 'SimHash', value: data?.sim_hash || '--', copy: !!data },
    { label: '文本长度', value: data?.text_length ?? '--', copy: !!data },
    { label: '价格', value: `${form.price || 0} EDU` },
    { label: '上传奖励', value: data ? `+${data.upload_reward || 0} EDU` : '--' },
    { label: '交易哈希', value: data?.tx_hash || '--', copy: !!data },
    { label: '上传时间', value: data?.uploaded_at || '--', copy: !!data },
    { label: '状态', value: data ? '已存证' : '未上传' },
  ]
})

function validateFile(file) {
  if (!file) return false
  const ext = `.${file.name.split('.').pop()?.toLowerCase()}`
  if (!acceptedTypes.split(',').includes(ext)) {
    showToast('仅支持 pdf、docx、pptx、txt、md 文件')
    return false
  }
  if (file.size > 50 * 1024 * 1024) {
    showToast('文件大小不能超过 50MB')
    return false
  }
  return true
}

function setFile(file) {
  if (!validateFile(file)) return
  selectedFile.value = file
  result.value = null
}

function handleFileChange(event) {
  setFile(event.target.files?.[0])
}

function handleDrop(event) {
  isDragging.value = false
  setFile(event.dataTransfer.files?.[0])
}

async function handleUpload() {
  if (!canSubmit.value) {
    showToast('请先选择文件并填写课程编号')
    return
  }

  loading.value = true
  try {
    const data = new FormData()
    data.append('file', selectedFile.value)
    data.append('name', selectedFile.value.name)
    data.append('course', form.course)
    data.append('price', String(form.price))
    data.append('policy_type', String({ public: 0, 'same-course': 1, whitelist: 2 }[form.policy] ?? 0))
    data.append('policy_value', form.policy === 'whitelist' ? whitelistAddresses.value.join(',') : '')
    const res = await api.postForm('/api/material/upload', data)
    result.value = {
      ...res.data,
      uploaded_at: formatTime(Date.now()),
    }
    await auth.refreshBalance()
    showToast('上传成功，资料已完成链上存证')
  } catch (error) {
    showToast(error.message || '上传失败')
  } finally {
    loading.value = false
  }
}

function resetForm() {
  selectedFile.value = null
  result.value = null
  form.course = ''
  form.price = 12
  form.policy = 'public'
  form.policyValue = ''
  if (fileInput.value) fileInput.value.value = ''
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function showToast(message) {
  toast.value = message
  window.clearTimeout(showToast.timer)
  showToast.timer = window.setTimeout(() => {
    toast.value = ''
  }, 1800)
}

async function copyValue(value, label) {
  const copied = await copyText(String(value ?? ''))
  showToast(copied ? `${label}已复制` : '复制失败，请手动复制')
}
</script>

<style scoped>
.upload-page {
  min-width: 1200px;
  min-height: 100vh;
  overflow-x: hidden;
  overflow-y: auto;
  color: var(--text-primary);
  background: #f4f7fa;
}

svg {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

button,
input,
select {
  font: inherit;
}

button {
  cursor: pointer;
}

.app-sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 20;
  width: 248px;
  overflow: hidden;
  background: linear-gradient(180deg, #003a70 0%, #002f60 48%, #00284f 100%);
  box-shadow: 8px 0 28px rgba(0, 39, 82, 0.2);
}

.sidebar-brand {
  padding: 34px 20px 26px;
}

.sidebar-brand img {
  width: 210px;
  height: 78px;
  object-fit: contain;
  object-position: left center;
}

.sidebar-brand p {
  margin: 14px 0 0;
  color: rgba(255, 255, 255, 0.86);
  font-size: 16px;
  font-weight: 600;
}

.sidebar-nav {
  position: relative;
  z-index: 2;
  display: grid;
  gap: 10px;
  padding: 0 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 15px;
  height: 60px;
  padding: 0 22px;
  color: rgba(255, 255, 255, 0.88);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 700;
  text-align: left;
}

.nav-item:disabled {
  cursor: default;
}

.nav-item.active {
  color: #ffffff;
  background: linear-gradient(135deg, #0079ba 0%, #005f92 100%);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 12px 24px rgba(0, 36, 90, 0.22);
}

.nav-item span,
.nav-item :deep(svg) {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
}

.nav-item :deep(svg) {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.sidebar-bridge {
  position: absolute;
  left: -52px;
  right: 0;
  bottom: 96px;
  height: 210px;
  opacity: 0.2;
  border-top: 1px solid rgba(209, 232, 255, 0.35);
  border-bottom: 1px solid rgba(209, 232, 255, 0.25);
  border-radius: 50%;
  transform: rotate(-8deg);
}

.sidebar-watermark {
  position: absolute;
  z-index: 1;
  width: 340px;
  height: 340px;
  right: -118px;
  bottom: 148px;
  object-fit: contain;
  opacity: 0.1;
  pointer-events: none;
  transform: rotate(-10deg);
  filter: drop-shadow(0 22px 42px rgba(0, 0, 0, 0.16));
}

.sidebar-bridge::before,
.sidebar-bridge::after {
  position: absolute;
  left: -80px;
  width: 380px;
  height: 120px;
  content: '';
  border-top: 1px solid rgba(209, 232, 255, 0.28);
  border-radius: 50%;
}

.sidebar-bridge::before { top: 40px; }
.sidebar-bridge::after { top: 84px; }

.chain-local {
  position: absolute;
  left: 30px;
  right: 26px;
  bottom: 30px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #ffffff;
  font-size: 16px;
}

.chain-local svg {
  width: 18px;
  height: 18px;
  margin-left: auto;
}

.status-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #16a34a;
  box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.12);
}

.app-header {
  position: fixed;
  top: 0;
  left: 248px;
  right: 0;
  z-index: 15;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 72px;
  padding: 0 14px 0 30px;
  background: rgba(255, 255, 255, 0.94);
  border-bottom: 1px solid #dce4ef;
  backdrop-filter: blur(14px);
}

.app-header h1 {
  margin: 0;
  color: #10233f;
  font-size: 30px;
  font-weight: 800;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-button {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  color: #10233f;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 8px;
}

.icon-button svg {
  width: 22px;
  height: 22px;
}

.chain-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-left: 16px;
  border-left: 1px solid #dce4ef;
  color: #53647c;
  font-size: 14px;
}

.chain-status strong {
  color: #10233f;
}

.user-card {
  display: grid;
  grid-template-columns: 48px 126px 100px 170px 82px;
  align-items: center;
  min-height: 58px;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 8px;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
}

.avatar {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  margin-left: 12px;
  color: #2f6fbc;
  background: #e8f2ff;
  border-radius: 50%;
}

.avatar svg {
  width: 25px;
  height: 25px;
  fill: currentColor;
  stroke: none;
}

.user-main,
.user-metric,
.user-address {
  display: grid;
  gap: 4px;
  height: 58px;
  align-content: center;
  padding: 0 14px;
  border-left: 1px solid #e5e7eb;
}

.user-main {
  border-left: none;
}

.user-main strong,
.user-address strong {
  color: #10233f;
  font-size: 15px;
}

.user-main span,
.user-metric span,
.user-address span {
  color: #53647c;
  font-size: 12px;
}

.user-metric strong {
  color: #0079ba;
  font-size: 17px;
}

.user-address {
  grid-template-columns: 1fr auto;
}

.user-address span,
.user-address strong {
  grid-column: 1;
}

.user-address button {
  grid-column: 2;
  grid-row: 1 / span 2;
  color: #53647c;
  background: transparent;
  border: none;
}

.user-address svg {
  width: 18px;
  height: 18px;
}

.logout-button {
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: #10233f;
  background: #ffffff;
  border: none;
  border-left: 1px solid #e5e7eb;
  font-size: 14px;
}

.logout-button svg {
  width: 18px;
  height: 18px;
}

.upload-content {
  min-height: 100vh;
  padding: 88px 16px 28px 264px;
  display: grid;
  grid-template-columns: minmax(590px, 1fr) 520px;
  gap: 16px;
  align-items: start;
}

.upload-main {
  min-width: 0;
  display: grid;
  grid-template-rows: auto auto auto;
  align-content: start;
  gap: 12px;
}

.hero-card,
.form-card,
.progress-card,
.result-card,
.similar-card,
.notice-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}

.hero-card {
  min-height: 122px;
  display: flex;
  align-items: center;
  padding: 0 28px;
  position: relative;
  overflow: hidden;
}

.hero-card::before {
  position: absolute;
  inset: 20px 20px auto auto;
  width: 340px;
  height: 86px;
  content: '';
  border-top: 1px solid rgba(0, 121, 186, 0.13);
  border-bottom: 1px solid rgba(0, 121, 186, 0.08);
  border-radius: 50%;
  transform: rotate(-8deg);
}

.hero-card h2 {
  margin: 0 0 12px;
  color: #10233f;
  font-size: 28px;
  font-weight: 800;
}

.hero-card p {
  margin: 0;
  color: #53647c;
  font-size: 15px;
}

.form-card {
  padding: 20px;
}

.drop-zone {
  min-height: 224px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 12px;
  color: #10233f;
  background: #f7fbff;
  border: 2px dashed #9fc7f1;
  border-radius: 8px;
  text-align: center;
  transition: 0.2s;
}

.drop-zone.dragging,
.drop-zone:hover {
  border-color: #0079ba;
  box-shadow: 0 0 0 4px rgba(0, 121, 186, 0.1);
}

.drop-zone.filled {
  background: #eef8ff;
}

.upload-icon {
  width: 70px;
  height: 70px;
  display: grid;
  place-items: center;
  color: #0079ba;
  background: #ffffff;
  border-radius: 50%;
  box-shadow: 0 14px 34px rgba(0, 121, 186, 0.14);
}

.upload-icon svg {
  width: 42px;
  height: 42px;
}

.drop-zone strong {
  color: #003a70;
  font-size: 18px;
}

.drop-zone p {
  margin: 0;
  color: #53647c;
  font-size: 14px;
}

.select-button {
  height: 40px;
  padding: 0 28px;
  color: #0079ba;
  background: #ffffff;
  border: 1px solid #0079ba;
  border-radius: 6px;
  font-weight: 700;
}

.field {
  display: grid;
  gap: 9px;
  margin-top: 18px;
}

.field span,
.policy-group legend {
  color: #10233f;
  font-size: 14px;
  font-weight: 800;
}

.field select,
.number-shell {
  width: 100%;
  height: 42px;
  color: #10233f;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 7px;
  outline: none;
}

.field select {
  padding: 0 14px;
}

.number-shell {
  display: grid;
  grid-template-columns: 1fr 70px;
  align-items: center;
}

.number-shell input {
  min-width: 0;
  height: 40px;
  padding: 0 12px;
  color: #10233f;
  border: none;
  outline: none;
}

.number-shell span {
  display: grid;
  place-items: center;
  height: 40px;
  color: #53647c;
  border-left: 1px solid #dce4ef;
}

.policy-group {
  display: grid;
  gap: 12px;
  margin: 18px 0 0;
  padding: 0;
  border: none;
}

.policy-group label {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 28px;
}

.policy-group input {
  width: 18px;
  height: 18px;
  accent-color: #0079ba;
}

.policy-group span {
  min-width: 66px;
  color: #10233f;
  font-weight: 700;
}

.policy-group em {
  padding: 3px 10px;
  color: #15803d;
  background: #dcfce7;
  border-radius: 999px;
  font-size: 12px;
  font-style: normal;
}

.policy-group label:nth-of-type(2) em {
  color: #b45309;
  background: #fef3c7;
}

.policy-group .disabled {
  color: #9ca3af;
}

.policy-group .disabled span {
  color: #9ca3af;
}

.policy-group .disabled em {
  color: #6b7280;
  background: #e5e7eb;
}

.submit-button {
  width: 100%;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  margin-top: 20px;
  color: #ffffff;
  background: linear-gradient(180deg, #0079ba 0%, #005f92 100%);
  border: 1px solid #00649a;
  border-radius: 6px;
  box-shadow: 0 8px 18px rgba(0, 121, 186, 0.22);
  font-size: 16px;
  font-weight: 800;
}

.submit-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.submit-button svg {
  width: 20px;
  height: 20px;
}

.progress-card {
  padding: 18px 26px 22px;
}

.progress-card h2,
.result-card h2,
.similar-card h2 {
  margin: 0 0 18px;
  color: #10233f;
  font-size: 18px;
  font-weight: 800;
}

.steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  text-align: center;
}

.step {
  position: relative;
  display: grid;
  gap: 8px;
  color: #8a97aa;
}

.step:not(:last-child)::after {
  position: absolute;
  left: calc(50% + 28px);
  top: 16px;
  width: calc(100% - 56px);
  height: 1px;
  content: '';
  background: #dce4ef;
}

.step span {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  justify-self: center;
  color: #53647c;
  background: #e5e7eb;
  border-radius: 50%;
  font-weight: 800;
}

.step.active span,
.step.done span {
  color: #ffffff;
  background: #0079ba;
  box-shadow: 0 8px 18px rgba(0, 121, 186, 0.18);
}

.step strong {
  color: #53647c;
  font-size: 14px;
}

.step.active strong,
.step.done strong {
  color: #0079ba;
}

.step p {
  margin: 0;
  font-size: 12px;
}

.result-panel {
  min-width: 0;
  position: sticky;
  top: 88px;
  height: calc(100vh - 104px);
  overflow: auto;
  display: grid;
  align-content: start;
  gap: 12px;
}

.result-card,
.similar-card {
  padding: 18px;
}

.success-banner,
.pending-banner {
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: 12px;
  align-items: center;
  min-height: 74px;
  padding: 0 16px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.success-banner {
  color: #15803d;
  background: #ecfdf5;
  border: 1px solid #bbf7d0;
}

.pending-banner {
  color: #0079ba;
  background: #e6f4fa;
  border: 1px solid #bfdbfe;
}

.success-banner svg,
.pending-banner svg {
  width: 32px;
  height: 32px;
}

.success-banner p,
.pending-banner p {
  margin: 6px 0 0;
  color: #53647c;
  font-size: 13px;
}

.result-list {
  margin: 0;
}

.result-list div {
  display: grid;
  grid-template-columns: 120px 1fr;
  align-items: center;
  min-height: 36px;
  border-bottom: 1px solid #e5e7eb;
}

.result-list dt {
  color: #53647c;
  font-size: 14px;
}

.result-list dd {
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  color: #10233f;
  font-size: 14px;
  text-align: right;
}

.result-list button {
  width: 24px;
  height: 24px;
  color: #53647c;
  background: transparent;
  border: none;
}

.result-list svg {
  width: 17px;
  height: 17px;
}

.similar-card h2 span {
  color: #53647c;
  font-weight: 500;
}

.similar-card table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.similar-card th,
.similar-card td {
  height: 34px;
  padding: 0 9px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.similar-card th {
  color: #53647c;
  background: #f9fafb;
  font-weight: 800;
}

.similar-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  border-radius: 999px;
  font-weight: 800;
}

.similar-tag.same {
  color: #15803d;
  background: #dcfce7;
}

.similar-tag.high {
  color: #b45309;
  background: #fef3c7;
}

.similar-tag.derived {
  color: #0079ba;
  background: #e6f4fa;
}

.similar-tag.low {
  color: #6b7280;
  background: #e5e7eb;
}

.similar-empty {
  display: grid;
  place-items: center;
  min-height: 96px;
  color: #53647c;
  background: #f9fafb;
  border-radius: 8px;
}

.notice-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 54px;
  padding: 0 14px;
  color: #9a5c00;
  background: #fff7ed;
  border-color: #fdba74;
}

.notice-card strong {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
}

.notice-card p {
  margin: 0;
  color: #53647c;
  font-size: 12px;
}

.notice-card button {
  flex: 0 0 auto;
  color: #0079ba;
  background: transparent;
  border: none;
  font-weight: 800;
}

.panel-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.primary-action,
.secondary-action {
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 800;
}

.primary-action {
  color: #ffffff;
  background: linear-gradient(180deg, #0079ba 0%, #005f92 100%);
  border: 1px solid #00649a;
}

.primary-action:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.secondary-action {
  color: #0079ba;
  background: #ffffff;
  border: 1px solid #0079ba;
}

.primary-action svg,
.secondary-action svg {
  width: 19px;
  height: 19px;
}

.toast {
  position: fixed;
  left: 50%;
  bottom: 28px;
  z-index: 50;
  transform: translateX(-50%);
  padding: 10px 18px;
  color: #ffffff;
  background: rgba(16, 35, 63, 0.92);
  border-radius: 999px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18);
  font-size: 14px;
}

.upload-page {
  min-width: 0;
  min-height: calc(100vh - var(--header-height));
  overflow: visible;
}

.upload-content {
  min-height: calc(100vh - var(--header-height));
  padding: 16px;
}

.whitelist-field textarea {
  width: 100%;
  resize: vertical;
  padding: 10px 12px;
  color: #10233f;
  background: #fff;
  border: 1px solid #dce4ef;
  border-radius: 6px;
  font: inherit;
  line-height: 1.5;
}

.whitelist-field small {
  color: #16803a;
}

.whitelist-field small.invalid {
  color: #c2410c;
}

.similar-empty-row {
  height: 72px;
  color: #7a889b;
  text-align: center;
}

.rules-backdrop {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(9, 25, 48, 0.48);
  backdrop-filter: blur(3px);
}

.rules-dialog {
  width: min(560px, 100%);
  padding: 24px;
  color: #10233f;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 24px 70px rgba(9, 25, 48, 0.28);
}

.rules-dialog header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rules-dialog h2 {
  margin: 0;
}

.rules-dialog header button {
  width: 36px;
  height: 36px;
  color: #53647c;
  background: transparent;
  border: 0;
  font-size: 28px;
}

.rules-dialog ol {
  display: grid;
  gap: 12px;
  margin: 22px 0;
  padding-left: 24px;
  color: #53647c;
  line-height: 1.65;
}

.rules-dialog > .primary-action {
  width: 100%;
}

@media (max-width: 1450px) {
  .upload-content {
    grid-template-columns: minmax(0, 1fr) 460px;
  }

  .upload-main,
  .result-panel {
    min-width: 0;
  }

  .similar-card {
    overflow-x: auto;
  }
}
</style>
