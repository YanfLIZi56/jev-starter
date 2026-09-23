<template>
  <div class="app">
    <div class="app-bg" aria-hidden="true"></div>

    <header class="header">
      <div class="brand">
        <div class="logo">J</div>
        <div class="brand-text">
          <h1>Jev 结构化问答控制台</h1>
          <p class="subtitle">Noul · Choice · Score · 多问题并行评估</p>
        </div>
      </div>

      <div class="header-key">
        <label class="header-key-label">填写你的 TypeSafe API Key</label>
        <div class="key-row">
          <input v-model="apiKey" type="password" placeholder="sk-..." autocomplete="off" />
          <label class="remember" title="仅保存在本机浏览器">
            <input v-model="rememberKey" type="checkbox" />
            <span class="remember-mark"></span>
            <span class="remember-text">记住</span>
          </label>
        </div>
      </div>
    </header>

    <main class="main">
      <!-- 左侧：输入 -->
      <section class="panel">
        <div class="panel-head">
          <h2>输入</h2>
          <span class="panel-tag">Input</span>
        </div>

        <!-- State（可折叠） -->
        <div class="card collapsible">
          <div class="collapsible-head" @click="stateOpen = !stateOpen">
            <div class="card-title" style="margin-bottom: 0">
              <span class="dot-icon"></span>
              <label style="margin: 0; cursor: pointer">
                State · 被评估的上下文
              </label>
              <span class="optional">选填</span>
            </div>
            <span class="chevron" :class="{ open: stateOpen }">›</span>
          </div>
          <div class="collapsible-body" :class="{ open: stateOpen }">
            <div>
              <textarea v-model="state" rows="3" placeholder="留空则省略 state，模型仅根据每个问题的 instructions 独立作答。"
                style="margin-top: 12px" />
            </div>
          </div>
        </div>

        <!-- 操作栏 -->
        <div class="topbar">
          <button class="btn ghost" @click="addQuestion">
            <span class="plus">+</span> 新增问题
          </button>
          <button class="btn ghost" @click="loadExample">填入示例</button>
          <button class="btn ghost" @click="openExport">导出代码</button>
          <button class="btn ghost" @click="openImport">导入配置</button>
          <button class="btn ghost danger" @click="clearAll">清空全部</button>
        </div>

        <!-- 问题列表 -->
        <div v-for="(q, qi) in questions" :key="q._id" class="card question">
          <div class="q-header">
            <span class="q-index">
              <span class="q-num">{{ String(qi + 1).padStart(2, '0') }}</span>
              问题
            </span>
            <button v-if="questions.length > 1" class="icon-btn" title="删除" @click="removeQuestion(qi)">
              ✕
            </button>
          </div>

          <div class="field">
            <label>问题名称（唯一标识）</label>
            <input v-model="q.name" type="text" placeholder="例如：sentiment" />
            <div v-if="nameError(qi)" class="hint err">{{ nameError(qi) }}</div>
          </div>

          <div class="field">
            <label>类型</label>
            <div class="tabs">
              <button class="tab" :class="{ active: q.type === 'noul' }" @click="q.type = 'noul'">
                <span class="tab-name">Noul</span>
                <span class="tab-desc">概率</span>
              </button>
              <button class="tab" :class="{ active: q.type === 'choice' }" @click="q.type = 'choice'">
                <span class="tab-name">Choice</span>
                <span class="tab-desc">分类</span>
              </button>
              <button class="tab" :class="{ active: q.type === 'score' }" @click="q.type = 'score'">
                <span class="tab-name">Score</span>
                <span class="tab-desc">评分</span>
              </button>
            </div>
          </div>

          <div class="field">
            <label>Instructions</label>
            <textarea v-model="q.instructions" rows="2" :placeholder="instructionsPlaceholder(q.type)" />
          </div>

          <!-- Choice -->
          <template v-if="q.type === 'choice'">
            <div class="field">
              <label>Criteria · 标签 : 描述</label>
              <div v-for="(item, ki) in q.criteriaMap" :key="ki" class="kv-row">
                <input v-model="item.key" type="text" placeholder="标签" />
                <input v-model="item.value" type="text" placeholder="描述" />
                <button class="icon-btn" @click="q.criteriaMap.splice(ki, 1)">✕</button>
              </div>
              <button class="btn ghost small" @click="q.criteriaMap.push({ key: '', value: '' })">
                + 添加选项
              </button>
            </div>
          </template>

          <!-- Score -->
          <template v-if="q.type === 'score'">
            <div class="field">
              <label>Criteria · 有序层级（从低到高）</label>
              <div v-for="(item, ki) in q.criteriaList" :key="ki" class="kv-row">
                <span class="level-badge">{{ ki + 1 }}</span>
                <input v-model="q.criteriaList[ki]" type="text" placeholder="层级描述" />
                <button class="icon-btn" @click="q.criteriaList.splice(ki, 1)">✕</button>
              </div>
              <button class="btn ghost small" @click="q.criteriaList.push('')">
                + 添加层级
              </button>
            </div>
          </template>
        </div>

        <button class="submit" :disabled="loading" @click="submit">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? '请求中…' : '提交请求' }}
        </button>
      </section>

      <!-- 右侧：输出 -->
      <section class="panel">
        <div class="panel-head">
          <h2>输出</h2>
          <span class="panel-tag" :class="{ 'tag-error': error }">
            {{ error ? 'Error' : 'Output' }}
          </span>
        </div>

        <transition name="fade">
          <div v-if="error" class="error">
            <span class="error-icon">!</span>
            <div class="error-text">{{ error }}</div>
          </div>
        </transition>

        <!-- 空状态：只有 无错误 且 未加载 且 无结果 时显示 -->
        <div v-if="!result && !loading && !error" class="empty">
          <div class="empty-icon">◎</div>
          <p>提交后结果将显示在这里</p>
        </div>

        <!-- 加载中 -->
        <div v-if="loading" class="empty">
          <div class="spinner large"></div>
          <p>模型正在思考…</p>
        </div>

        <template v-if="result && !loading">
          <div v-for="(ans, idx) in result.answers" :key="ans.name" class="answer"
            :style="{ '--delay': idx * 60 + 'ms' }">
            <div class="answer-head">
              <span class="answer-name">{{ ans.name }}</span>
              <span class="answer-type" :data-type="ans.type">{{ ans.type }}</span>
            </div>

            <!-- Noul -->
            <template v-if="ans.type === 'noul'">
              <div class="noul-wrap">
                <div class="answer-main big">{{ pct(ans.answer_value) }}</div>
                <div class="ring" :style="{ '--p': (ans.answer_value || 0) * 360 + 'deg' }"></div>
              </div>
              <div class="answer-desc">为「是」的概率</div>
            </template>

            <!-- Choice -->
            <template v-else-if="ans.type === 'choice'">
              <div class="answer-main">{{ ans.answer_label || '—' }}</div>
              <div v-if="ans.answer_description" class="answer-desc">
                {{ ans.answer_description }}
              </div>
              <div v-if="ans.probabilities" class="prob-bar">
                <div v-for="(p, k, i) in ans.probabilities" :key="k" class="prob-seg"
                  :style="{ width: p * 100 + '%', background: colorForIndex(i) }" />
              </div>
              <div v-if="ans.probabilities" class="prob-legend">
                <span v-for="(p, k, i) in ans.probabilities" :key="k">
                  <i class="dot" :style="{ background: colorForIndex(i) }" />
                  <span class="legend-key">{{ k }}</span>
                  <span class="legend-val">{{ pct(p) }}</span>
                </span>
              </div>
            </template>

            <!-- Score -->
            <template v-else-if="ans.type === 'score'">
              <div class="answer-main">
                {{ ans.answer_value }}
                <span v-if="ans.answer_label" class="answer-label">
                  / {{ ans.answer_label }}
                </span>
              </div>
              <div v-if="ans.probabilities" class="prob-bar">
                <div v-for="(p, k, i) in ans.probabilities" :key="k" class="prob-seg"
                  :style="{ width: p * 100 + '%', background: colorForIndex(i) }" />
              </div>
              <div v-if="ans.probabilities" class="prob-legend">
                <span v-for="(p, k, i) in ans.probabilities" :key="k">
                  <i class="dot" :style="{ background: colorForIndex(i) }" />
                  <span class="legend-key">{{ (ans.legend && ans.legend[k]) || k }}</span>
                  <span class="legend-val">{{ pct(p) }}</span>
                </span>
              </div>
            </template>
          </div>

          <div class="meta">
            <div class="meta-item">
              <span class="meta-label">模型</span>
              <span class="meta-val">{{ result.model }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">请求耗时</span>
              <span class="meta-val">{{ result.latency_ms }} ms</span>
            </div>
            <div v-if="result.usage" class="meta-item">
              <span class="meta-label">Token</span>
              <span class="meta-val">
                {{ result.usage.input_tokens ?? '-' }} in ·
                {{ result.usage.output_tokens ?? '-' }} out
              </span>
            </div>
          </div>
        </template>
      </section>
    </main>

    <!-- ============ 导出模态框 ============ -->
    <transition name="fade">
      <div v-if="showExport" class="modal-mask" @click.self="showExport = false">
        <div class="modal">
          <div class="modal-head">
            <h3>导出代码</h3>
            <button class="icon-btn" @click="showExport = false">✕</button>
          </div>

          <div class="modal-tabs">
            <button v-for="fmt in formats" :key="fmt.id" class="modal-tab" :class="{ active: exportFormat === fmt.id }"
              @click="exportFormat = fmt.id">
              {{ fmt.label }}
            </button>
          </div>

          <div class="modal-body">
            <pre class="code-block"><code>{{ exportedCode }}</code></pre>
          </div>

          <div class="modal-foot">
            <span v-if="exportWarn" class="hint err" style="margin-right: auto">
              {{ exportWarn }}
            </span>
            <button class="btn ghost" @click="showExport = false">关闭</button>
            <button class="btn" @click="copyExport">
              {{ copySuccess ? '✓ 已复制' : '复制' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ============ 导入模态框 ============ -->
    <transition name="fade">
      <div v-if="showImport" class="modal-mask" @click.self="showImport = false">
        <div class="modal">
          <div class="modal-head">
            <h3>导入配置</h3>
            <button class="icon-btn" @click="showImport = false">✕</button>
          </div>

          <div class="modal-body">
            <div class="import-tip">
              支持粘贴或上传 JSON 配置，格式与「导出 → JSON」一致。
            </div>

            <div class="import-actions">
              <label class="btn ghost small">
                选择 JSON 文件
                <input type="file" accept=".json,application/json" style="display: none" @change="onFileSelect" />
              </label>
              <span class="hint" style="margin: 0">或直接粘贴到下方</span>
            </div>

            <textarea v-model="importText" rows="10" placeholder='{
  "state": "...",
  "questions": {
    "sentiment": {
      "type": "choice",
      "instructions": "...",
      "criteria": { "pos": "...", "neg": "..." }
    }
  }
}' class="import-textarea" />

            <div v-if="importError" class="hint err" style="margin-top: 8px">
              {{ importError }}
            </div>
          </div>

          <div class="modal-foot">
            <button class="btn ghost" @click="showImport = false">取消</button>
            <button class="btn" @click="doImport">导入</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'
const STORAGE_KEY = 'jev_studio_snapshot_v5'
const KEY_STORAGE = 'jev_studio_apikey_v5'

let _uid = 0
const newQuestion = (overrides = {}) => ({
  _id: ++_uid,
  name: '',
  type: 'noul',
  instructions: '',
  criteriaMap: [
    { key: '', value: '' },
    { key: '', value: '' },
  ],
  criteriaList: ['', ''],
  ...overrides,
})

const EXAMPLE_QUESTIONS = [
  {
    name: 'is_urgent',
    type: 'noul',
    instructions: '这段文本是否表达了紧迫、需要立即处理的需求？',
  },
  {
    name: 'department',
    type: 'choice',
    instructions: '这条工单应该由哪个团队处理？',
    criteriaMap: [
      { key: 'billing', value: '付款、发票或订阅相关问题' },
      { key: 'technical', value: 'Bug、集成或技术故障' },
      { key: 'sales', value: '报价、账号或售前咨询' },
    ],
  },
  {
    name: 'frustration',
    type: 'score',
    instructions: '客户的愤怒程度如何？',
    criteriaList: ['冷静，仅陈述事实', '有些不满但克制', '非常愤怒，用词激烈'],
  },
]

const apiKey = ref('')
const rememberKey = ref(false)
const state = ref('')
const stateOpen = ref(false)
const questions = reactive([newQuestion()])
const loading = ref(false)
const error = ref('')
const result = ref(null)

// ---------- 导出 / 导入状态 ----------
const showExport = ref(false)
const exportFormat = ref('python')
const copySuccess = ref(false)
const showImport = ref(false)
const importText = ref('')
const importError = ref('')

const formats = [
  { id: 'python', label: 'Python' },
  { id: 'javascript', label: 'JavaScript' },
  { id: 'curl', label: 'cURL' },
  { id: 'json', label: 'JSON' },
]

// ---------- 校验 ----------
const nameError = (idx) => {
  const name = questions[idx].name.trim()
  if (!name) return '名称不能为空'
  if (questions.some((q, i) => i !== idx && q.name.trim() === name)) return '名称重复'
  return ''
}

const addQuestion = () => questions.push(newQuestion())
const removeQuestion = (idx) => questions.splice(idx, 1)

const clearAll = () => {
  if (!confirm('清空所有已填写的内容？')) return
  state.value = ''
  stateOpen.value = false
  questions.splice(0, questions.length, newQuestion())
  result.value = null
  error.value = ''
}

const loadExample = () => {
  state.value =
    "Hi, I've been trying to connect my Stripe account for 3 days. " +
    'The dashboard keeps showing an error and I need to issue refunds today. ' +
    'This is blocking my whole team.'
  stateOpen.value = true
  questions.splice(
    0,
    questions.length,
    ...EXAMPLE_QUESTIONS.map((q) =>
      newQuestion({
        name: q.name,
        type: q.type,
        instructions: q.instructions,
        criteriaMap: q.criteriaMap
          ? q.criteriaMap.map((it) => ({ ...it }))
          : [
            { key: '', value: '' },
            { key: '', value: '' },
          ],
        criteriaList: q.criteriaList ? [...q.criteriaList] : ['', ''],
      })
    )
  )
}

// ---------- 展示工具 ----------
const palette = [
  '#5b8cff',
  '#4ec9a8',
  '#e05c5c',
  '#d4a24e',
  '#c77dff',
  '#ffb45c',
  '#5ec8e5',
  '#7dd87d',
  '#f06292',
  '#a78bfa',
]
const colorForIndex = (i, total = palette.length) => {
  if (i < palette.length) return palette[i]
  const hue = (i * 137.508) % 360
  return `hsl(${hue}, 70%, 62%)`
}
const pct = (v) => (v == null ? '—' : (v * 100).toFixed(1) + '%')

const instructionsPlaceholder = (type) => {
  if (type === 'noul')
    return '描述一个可用概率回答的判断，例如：这条消息是否表达了紧急情绪？'
  if (type === 'choice')
    return '描述一个分类任务，例如：这条工单应由哪个团队处理？'
  return '描述一个评分任务，例如：客户的愤怒程度如何？'
}

// ---------- 导出代码生成 ----------
// 返回一份干净的、只包含有效配置的快照（跳过完全空白的问题）
const cleanQuestions = () => {
  const out = []
  for (const q of questions) {
    const name = q.name.trim()
    const inst = q.instructions.trim()
    // 空名称 + 空 instructions 视为未填写，跳过
    if (!name && !inst) continue
    out.push({
      name: name || `question_${out.length + 1}`,
      type: q.type,
      instructions: inst,
      criteriaMap: q.criteriaMap
        .filter((it) => it.key.trim())
        .map((it) => ({ key: it.key.trim(), value: it.value.trim() })),
      criteriaList: q.criteriaList.map((s) => s.trim()).filter(Boolean),
    })
  }
  return out
}

const exportedCode = computed(() => {
  const qs = cleanQuestions()
  const st = state.value.trim()

  if (exportFormat.value === 'python') {
    const L = []
    L.push('from typesafe_sdk import Choice, Noul, Score')
    L.push('')
    L.push('questions = {')
    for (const q of qs) {
      const nameLit = JSON.stringify(q.name)
      const instLit = JSON.stringify(q.instructions)
      if (q.type === 'noul') {
        L.push(`    ${nameLit}: Noul(`)
        L.push(`        instructions=${instLit},`)
        L.push('    ),')
      } else if (q.type === 'choice') {
        L.push(`    ${nameLit}: Choice(`)
        L.push(`        instructions=${instLit},`)
        L.push('        criteria={')
        for (const it of q.criteriaMap) {
          L.push(`            ${JSON.stringify(it.key)}: ${JSON.stringify(it.value)},`)
        }
        L.push('        },')
        L.push('    ),')
      } else if (q.type === 'score') {
        L.push(`    ${nameLit}: Score(`)
        L.push(`        instructions=${instLit},`)
        L.push('        criteria=[')
        for (const it of q.criteriaList) {
          L.push(`            ${JSON.stringify(it)},`)
        }
        L.push('        ],')
        L.push('    ),')
      }
    }
    L.push('}')
    L.push('')
    if (st) {
      L.push(`state = ${JSON.stringify(st)}`)
    } else {
      L.push('# state 可选，省略时模型仅根据 instructions 独立作答')
      L.push('state = None')
    }
    L.push('')
    L.push('response = client.system_one(state=state, questions=questions)')
    L.push('')
    L.push('# 访问结果：response.answers["问题名"].choice / .score / .noul')
    return L.join('\n')
  }

  if (exportFormat.value === 'javascript') {
    const L = []
    L.push('import { TypeSafeClient, choice, noul, score } from "@typesafe-ai/sdk";')
    L.push('')
    L.push('const questions = {')
    for (const q of qs) {
      const instLit = JSON.stringify(q.instructions)
      if (q.type === 'noul') {
        L.push(`  ${q.name}: noul(${instLit}),`)
      } else if (q.type === 'choice') {
        L.push(`  ${q.name}: choice(${instLit}, {`)
        for (const it of q.criteriaMap) {
          L.push(`    ${it.key}: ${JSON.stringify(it.value)},`)
        }
        L.push('  }),')
      } else if (q.type === 'score') {
        L.push(`  ${q.name}: score(${instLit}, [`)
        for (const it of q.criteriaList) {
          L.push(`    ${JSON.stringify(it)},`)
        }
        L.push('  ]),')
      }
    }
    L.push('};')
    L.push('')
    L.push('const client = new TypeSafeClient({ apiKey: process.env.TYPESAFE_API_KEY });')
    L.push('const response = await client.systemOne({')
    if (st) L.push(`  state: ${JSON.stringify(st)},`)
    L.push('  questions,')
    L.push('});')
    L.push('')
    L.push('// 访问结果：response.answers["问题名"].choice / .score / .noul')
    return L.join('\n')
  }

  if (exportFormat.value === 'curl') {
    const payload = { model: 'jev-latest', questions: {} }
    if (st) payload.state = st
    for (const q of qs) {
      const obj = { type: q.type, instructions: q.instructions }
      if (q.type === 'choice') {
        obj.criteria = {}
        for (const it of q.criteriaMap) obj.criteria[it.key] = it.value
      } else if (q.type === 'score') {
        obj.criteria = q.criteriaList
      }
      payload.questions[q.name] = obj
    }
    const json = JSON.stringify(payload, null, 2)
    // POSIX shell 单引号内的单引号需要特殊处理
    const safeJson = json.replace(/'/g, "'\\''")
    return [
      'curl -X POST https://api.typesafe.ai/v1/systemone \\',
      '  -H "Authorization: Bearer $TYPESAFE_API_KEY" \\',
      '  -H "Content-Type: application/json" \\',
      `  -d '${safeJson}'`,
    ].join('\n')
  }

  // JSON：与「导入配置」格式一致，可直接复用
  const payload = { questions: {} }
  if (st) payload.state = st
  for (const q of qs) {
    const obj = { type: q.type, instructions: q.instructions }
    if (q.type === 'choice') {
      obj.criteria = {}
      for (const it of q.criteriaMap) obj.criteria[it.key] = it.value
    } else if (q.type === 'score') {
      obj.criteria = q.criteriaList
    }
    payload.questions[q.name] = obj
  }
  return JSON.stringify(payload, null, 2)
})

const exportWarn = computed(() => {
  if (cleanQuestions().length === 0) return '当前没有问题配置，导出内容为空。'
  return ''
})

// ---------- 导出 / 导入交互 ----------
const openExport = () => {
  copySuccess.value = false
  showExport.value = true
}

const copyExport = async () => {
  const text = exportedCode.value
  try {
    await navigator.clipboard.writeText(text)
  } catch (_) {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    try {
      document.execCommand('copy')
    } catch (_) { }
    document.body.removeChild(ta)
  }
  copySuccess.value = true
  setTimeout(() => (copySuccess.value = false), 1600)
}

const openImport = () => {
  importText.value = ''
  importError.value = ''
  showImport.value = true
}

const onFileSelect = (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    importText.value = String(reader.result || '')
    importError.value = ''
  }
  reader.onerror = () => {
    importError.value = '文件读取失败'
  }
  reader.readAsText(file)
  // 允许再次选择同一文件
  e.target.value = ''
}

const doImport = () => {
  importError.value = ''
  let data
  try {
    data = JSON.parse(importText.value)
  } catch (e) {
    importError.value = `JSON 解析失败：${e.message}`
    return
  }

  if (!data || typeof data !== 'object' || !data.questions || typeof data.questions !== 'object') {
    importError.value = '缺少 questions 字段，或格式不正确。'
    return
  }

  const newQs = []
  for (const [name, cfg] of Object.entries(data.questions)) {
    if (!cfg || typeof cfg !== 'object') continue
    const type = cfg.type
    if (!['noul', 'choice', 'score'].includes(type)) continue

    const q = {
      name: String(name),
      type,
      instructions: String(cfg.instructions || ''),
      criteriaMap: [
        { key: '', value: '' },
        { key: '', value: '' },
      ],
      criteriaList: ['', ''],
    }

    if (type === 'choice' && cfg.criteria && typeof cfg.criteria === 'object') {
      const entries = Object.entries(cfg.criteria).map(([k, v]) => ({
        key: String(k),
        value: String(v ?? ''),
      }))
      if (entries.length) q.criteriaMap = entries
    }

    if (type === 'score' && Array.isArray(cfg.criteria)) {
      const list = cfg.criteria.map((s) => String(s ?? '')).filter(Boolean)
      if (list.length) q.criteriaList = list
    }

    newQs.push(newQuestion(q))
  }

  if (!newQs.length) {
    importError.value = '未找到有效的 questions 配置。'
    return
  }

  state.value = typeof data.state === 'string' ? data.state : ''
  stateOpen.value = !!state.value.trim()
  questions.splice(0, questions.length, ...newQs)
  showImport.value = false
  importText.value = ''
}

// ---------- 提交 ----------
const submit = async () => {
  error.value = ''
  result.value = null

  if (!apiKey.value.trim()) {
    error.value = '请填写 API Key'
    return
  }
  if (!questions.length) {
    error.value = '至少保留一个问题'
    return
  }

  for (let i = 0; i < questions.length; i++) {
    const q = questions[i]
    const ne = nameError(i)
    if (ne) {
      error.value = `问题 #${i + 1}：${ne}`
      return
    }
    if (!q.instructions.trim()) {
      error.value = `问题 #${i + 1}：Instructions 不能为空`
      return
    }
    if (q.type === 'choice') {
      const valid = q.criteriaMap.filter((it) => it.key.trim())
      if (valid.length < 2) {
        error.value = `问题 #${i + 1}：Choice 至少需要 2 个带标签的选项`
        return
      }
    }
    if (q.type === 'score') {
      const valid = q.criteriaList.filter((s) => s.trim())
      if (valid.length < 2) {
        error.value = `问题 #${i + 1}：Score 至少需要 2 个层级`
        return
      }
    }
  }

  const payload = {
    api_key: apiKey.value.trim(),
    questions: questions.map((q) => {
      const base = {
        name: q.name.trim(),
        type: q.type,
        instructions: q.instructions.trim(),
      }
      if (q.type === 'choice') {
        base.criteria_map = Object.fromEntries(
          q.criteriaMap
            .filter((it) => it.key.trim())
            .map((it) => [it.key.trim(), it.value.trim()])
        )
      }
      if (q.type === 'score') {
        base.criteria_list = q.criteriaList.map((s) => s.trim()).filter(Boolean)
      }
      return base
    }),
  }
  if (state.value.trim()) payload.state = state.value.trim()

  loading.value = true
  try {
    const { data } = await axios.post(`${API_BASE}/api/ask`, payload, {
      timeout: 60000,
    })
    result.value = data
    saveSnapshot()
  } catch (e) {
    if (e.response) {
      const d = e.response.data?.detail
      error.value = typeof d === 'string' ? d : JSON.stringify(d, null, 2)
    } else if (e.code === 'ERR_NETWORK') {
      error.value = `无法连接到后端服务，请确认 FastAPI 已在 ${API_BASE} 启动。`
    } else {
      error.value = e.message || '请求失败'
    }
  } finally {
    loading.value = false
  }
}

// ---------- localStorage ----------
const saveSnapshot = () => {
  try {
    const snap = {
      state: state.value,
      questions: questions.map((q) => ({
        name: q.name,
        type: q.type,
        instructions: q.instructions,
        criteriaMap: q.criteriaMap.map((it) => ({ ...it })),
        criteriaList: [...q.criteriaList],
      })),
      result: result.value,
      savedAt: Date.now(),
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(snap))

    if (rememberKey.value && apiKey.value) {
      localStorage.setItem(KEY_STORAGE, apiKey.value)
    } else {
      localStorage.removeItem(KEY_STORAGE)
    }
  } catch (_) { }
}

const loadSnapshot = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const snap = JSON.parse(raw)
      state.value = snap.state || ''
      stateOpen.value = !!state.value.trim()
      if (Array.isArray(snap.questions) && snap.questions.length) {
        questions.splice(
          0,
          questions.length,
          ...snap.questions.map((q) =>
            newQuestion({
              name: q.name || '',
              type: q.type || 'noul',
              instructions: q.instructions || '',
              criteriaMap: q.criteriaMap?.length
                ? q.criteriaMap
                : [
                  { key: '', value: '' },
                  { key: '', value: '' },
                ],
              criteriaList: q.criteriaList?.length ? q.criteriaList : ['', ''],
            })
          )
        )
      }
      if (snap.result) result.value = snap.result
    }
    const savedKey = localStorage.getItem(KEY_STORAGE)
    if (savedKey) {
      apiKey.value = savedKey
      rememberKey.value = true
    }
  } catch (_) { }
}

watch(questions, () => saveSnapshot(), { deep: true })
watch([state, rememberKey], () => saveSnapshot())
onMounted(loadSnapshot)
</script>

<style scoped>
.app {
  --bg: #0b0d12;
  --panel: rgba(22, 26, 35, 0.72);
  --panel-2: rgba(28, 33, 44, 0.7);
  --border: rgba(255, 255, 255, 0.07);
  --border-2: rgba(255, 255, 255, 0.12);
  --text: #eef0f6;
  --text-2: #a8b0c2;
  --muted: #6b7385;
  --accent: #6b8cff;
  --accent-2: #9db1ff;
  --accent-glow: rgba(107, 140, 255, 0.35);
  --danger: #ef5f6b;
  --ok: #4ec9a8;
  --radius: 16px;
  --radius-sm: 10px;

  position: relative;
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI',
    'PingFang SC', 'Microsoft YaHei', sans-serif;
  line-height: 1.6;
  padding: 28px 20px 80px;
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
}

.app-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(1000px 600px at 12% -8%, rgba(107, 140, 255, 0.14), transparent 60%),
    radial-gradient(900px 500px at 92% 0%, rgba(199, 125, 255, 0.1), transparent 55%),
    radial-gradient(700px 500px at 50% 120%, rgba(78, 201, 168, 0.07), transparent 60%);
}

.header,
.main {
  position: relative;
  z-index: 1;
  max-width: 1440px;
  margin-inline: auto;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 28px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 0 0 auto;
  min-width: 0;
}

.logo {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 20px;
  color: #fff;
  background: linear-gradient(135deg, #6b8cff, #a06bff);
  box-shadow: 0 8px 24px -6px var(--accent-glow);
  flex: 0 0 auto;
}

.brand-text {
  min-width: 0;
}

.header h1 {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  letter-spacing: -0.2px;
}

.subtitle {
  color: var(--text-2);
  font-size: 12.5px;
  margin: 2px 0 0;
  letter-spacing: 0.2px;
}

.header-key {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 0 1 380px;
  min-width: 240px;
}

.header-key-label {
  font-size: 11.5px;
  color: var(--text-2);
  letter-spacing: 0.3px;
  font-weight: 500;
  padding-left: 2px;
  margin: 0;
}

.key-row {
  display: flex;
  align-items: stretch;
  gap: 8px;
}

.key-row input {
  flex: 1;
  min-width: 0;
  background: rgba(10, 12, 17, 0.65);
  border: 1px solid var(--border-2);
  border-radius: 10px;
  color: var(--text);
  padding: 10px 14px;
  font-size: 13.5px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.18s, box-shadow 0.18s, background 0.18s;
}

.key-row input::placeholder {
  color: var(--muted);
}

.key-row input:focus {
  border-color: var(--accent);
  background: rgba(10, 12, 17, 0.9);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.remember {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  border: 1px solid var(--border-2);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
  font-size: 12.5px;
  color: var(--text-2);
  user-select: none;
  transition: all 0.15s;
  flex: 0 0 auto;
  white-space: nowrap;
}

.remember:hover {
  border-color: var(--accent);
  color: var(--text);
}

.remember input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.remember-mark {
  width: 14px;
  height: 14px;
  border: 1.5px solid var(--border-2);
  border-radius: 4px;
  display: grid;
  place-items: center;
  transition: all 0.15s;
  flex: 0 0 auto;
}

.remember input:checked~.remember-mark {
  background: var(--accent);
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.remember input:checked~.remember-mark::after {
  content: '';
  width: 3px;
  height: 7px;
  border-right: 1.5px solid #fff;
  border-bottom: 1.5px solid #fff;
  transform: rotate(45deg) translate(-1px, -1px);
}

.remember input:checked~.remember-text {
  color: var(--text);
}

@media (max-width: 820px) {
  .header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .header-key {
    flex: 0 0 auto;
  }
}

.main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 22px;
  align-items: start;
}

@media (max-width: 960px) {
  .main {
    grid-template-columns: 1fr;
  }
}

.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.04) inset,
    0 24px 48px -24px rgba(0, 0, 0, 0.6);
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.panel-head h2 {
  font-size: 15px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 0.3px;
}

.panel-tag {
  font-size: 10.5px;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: var(--muted);
  border: 1px solid var(--border);
  padding: 3px 8px;
  border-radius: 6px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.card {
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 16px;
  margin-bottom: 14px;
  transition: border-color 0.2s;
}

.card:hover {
  border-color: var(--border-2);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.card-title label {
  margin: 0;
}

.dot-icon {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--muted);
  flex: 0 0 auto;
}

.dot-icon.accent {
  background: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.optional {
  font-size: 11px;
  color: var(--muted);
  border: 1px solid var(--border);
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: auto;
}

label {
  display: block;
  font-size: 12px;
  color: var(--text-2);
  margin-bottom: 7px;
  letter-spacing: 0.2px;
  font-weight: 500;
}

input[type='text'],
input[type='password'],
textarea {
  width: 100%;
  background: rgba(10, 12, 17, 0.6);
  border: 1px solid var(--border);
  border-radius: 9px;
  color: var(--text);
  padding: 10px 13px;
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.18s, box-shadow 0.18s, background 0.18s;
}

input[type='text']::placeholder,
input[type='password']::placeholder,
textarea::placeholder {
  color: var(--muted);
}

input:focus,
textarea:focus {
  border-color: var(--accent);
  background: rgba(10, 12, 17, 0.85);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

textarea {
  resize: vertical;
  min-height: 56px;
}

.collapsible {
  padding: 14px 16px;
  transition: padding 0.25s;
}

.collapsible-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}

.collapsible-head:hover .chevron {
  color: var(--accent);
}

.chevron {
  font-size: 20px;
  line-height: 1;
  color: var(--muted);
  transition: transform 0.25s ease, color 0.15s;
  transform: rotate(90deg);
  display: inline-block;
  width: 20px;
  text-align: center;
  flex: 0 0 auto;
}

.chevron.open {
  transform: rotate(270deg);
}

.collapsible-body {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.28s ease;
}

.collapsible-body.open {
  grid-template-rows: 1fr;
}

.collapsible-body>div {
  overflow: hidden;
}

.topbar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.btn {
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 9px;
  padding: 10px 16px;
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s, box-shadow 0.18s;
  font-family: inherit;
}

.btn:hover {
  background: var(--accent-2);
}

.btn:active {
  transform: translateY(1px);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.ghost {
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-2);
  border: 1px solid var(--border-2);
  font-weight: 500;
}

.btn.ghost:hover {
  color: var(--text);
  border-color: var(--accent);
  background: rgba(107, 140, 255, 0.08);
}

.btn.ghost.danger:hover {
  color: var(--danger);
  border-color: var(--danger);
  background: rgba(239, 95, 107, 0.08);
}

.btn.small {
  padding: 7px 12px;
  font-size: 12.5px;
}

.btn .plus {
  font-weight: 700;
  margin-right: 2px;
}

.icon-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--muted);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  display: grid;
  place-items: center;
  transition: all 0.15s;
  flex: 0 0 auto;
  font-family: inherit;
  padding: 0;
}

.icon-btn:hover {
  color: var(--danger);
  border-color: var(--danger);
  background: rgba(239, 95, 107, 0.08);
}

.submit {
  width: 100%;
  margin-top: 4px;
  padding: 13px 20px;
  border: none;
  border-radius: 11px;
  background: linear-gradient(135deg, #6b8cff, #8f6bff);
  color: #fff;
  font-size: 14.5px;
  font-weight: 700;
  letter-spacing: 0.3px;
  cursor: pointer;
  font-family: inherit;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 12px 30px -10px var(--accent-glow);
  transition: transform 0.1s, box-shadow 0.2s, filter 0.2s;
}

.submit:hover:not(:disabled) {
  filter: brightness(1.08);
  box-shadow: 0 16px 38px -10px var(--accent-glow);
}

.submit:active:not(:disabled) {
  transform: translateY(1px);
}

.submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex: 0 0 auto;
}

.spinner.large {
  width: 26px;
  height: 26px;
  border-width: 2.5px;
  border-color: rgba(107, 140, 255, 0.2);
  border-top-color: var(--accent);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.q-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.q-index {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 12px;
  color: var(--text-2);
  font-weight: 600;
  letter-spacing: 0.4px;
}

.q-num {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px;
  color: var(--accent);
  background: rgba(107, 140, 255, 0.12);
  border: 1px solid rgba(107, 140, 255, 0.25);
  padding: 1px 7px;
  border-radius: 5px;
}

.field {
  margin-top: 14px;
}

.field:first-of-type {
  margin-top: 0;
}

.tabs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  padding: 4px;
  background: rgba(10, 12, 17, 0.5);
  border: 1px solid var(--border);
  border-radius: 11px;
}

.tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  padding: 8px 6px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.18s;
  font-family: inherit;
}

.tab:hover:not(.active) {
  color: var(--text);
  background: rgba(255, 255, 255, 0.04);
}

.tab.active {
  background: linear-gradient(135deg, rgba(107, 140, 255, 0.9), rgba(143, 107, 255, 0.9));
  color: #fff;
  box-shadow: 0 4px 14px -4px var(--accent-glow);
}

.tab-name {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.tab-desc {
  font-size: 10.5px;
  opacity: 0.75;
  letter-spacing: 0.4px;
}

.tab.active .tab-desc {
  opacity: 0.9;
}

.kv-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}

.kv-row input {
  flex: 1;
  min-width: 0;
}

.level-badge {
  width: 26px;
  height: 26px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  font-size: 11.5px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: var(--accent);
  background: rgba(107, 140, 255, 0.1);
  border: 1px solid rgba(107, 140, 255, 0.22);
  border-radius: 7px;
}

.hint {
  font-size: 12px;
  color: var(--muted);
  margin-top: 5px;
}

.hint.err {
  color: var(--danger);
}

.error {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  background: rgba(239, 95, 107, 0.08);
  border: 1px solid rgba(239, 95, 107, 0.35);
  color: #ffc4c9;
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 13px;
  margin-top: 14px;
}

.error-icon {
  flex: 0 0 auto;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--danger);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 800;
  margin-top: 1px;
}

.error-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--muted);
  font-size: 13.5px;
  padding: 64px 20px;
  text-align: center;
  border: 1px dashed var(--border-2);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.01);
}

.empty-icon {
  font-size: 34px;
  color: var(--border-2);
  line-height: 1;
}

.empty p {
  margin: 0;
}

.answer {
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 16px;
  margin-bottom: 12px;
  animation: slideUp 0.35s ease both;
  animation-delay: var(--delay, 0ms);
  transition: border-color 0.2s;
}

.answer:hover {
  border-color: var(--border-2);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.answer-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}

.answer-name {
  font-weight: 700;
  color: var(--text);
  font-size: 14.5px;
  word-break: break-all;
  letter-spacing: 0.2px;
}

.answer-type {
  font-size: 10.5px;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 6px;
  flex: 0 0 auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  border: 1px solid var(--border-2);
  color: var(--text-2);
}

.answer-type[data-type='noul'] {
  color: #9db1ff;
  border-color: rgba(107, 140, 255, 0.35);
  background: rgba(107, 140, 255, 0.1);
}

.answer-type[data-type='choice'] {
  color: #7de0c4;
  border-color: rgba(78, 201, 168, 0.35);
  background: rgba(78, 201, 168, 0.1);
}

.answer-type[data-type='score'] {
  color: #e8c887;
  border-color: rgba(212, 162, 78, 0.35);
  background: rgba(212, 162, 78, 0.1);
}

.answer-main {
  font-size: 22px;
  font-weight: 700;
  margin: 6px 0;
  letter-spacing: -0.3px;
}

.answer-main.big {
  font-size: 30px;
  background: linear-gradient(135deg, #9db1ff, #c9a8ff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.noul-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.ring {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  flex: 0 0 auto;
  background: conic-gradient(var(--accent) var(--p, 0deg),
      rgba(255, 255, 255, 0.06) var(--p, 0deg));
  position: relative;
  mask: radial-gradient(circle, transparent 58%, #000 60%);
  -webkit-mask: radial-gradient(circle, transparent 58%, #000 60%);
}

.answer-label {
  font-weight: 500;
  color: var(--text-2);
  font-size: 15px;
}

.answer-desc {
  font-size: 13px;
  color: var(--text-2);
}

.prob-bar {
  display: flex;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  margin: 14px 0 10px;
  background: rgba(0, 0, 0, 0.35);
  gap: 1px;
}

.prob-seg {
  height: 100%;
  transition: width 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
  min-width: 2px;
}

.prob-legend {
  font-size: 12px;
  color: var(--text-2);
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
}

.prob-legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-key {
  color: var(--text-2);
}

.legend-val {
  color: var(--text);
  font-weight: 600;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11.5px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  flex: 0 0 auto;
}

.meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  margin-top: 20px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border);
  border-radius: 9px;
}

.meta-label {
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.4px;
  text-transform: uppercase;
}

.meta-val {
  font-size: 13.5px;
  color: var(--text);
  font-weight: 600;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.panel-tag.tag-error {
  color: var(--danger);
  border-color: rgba(239, 95, 107, 0.4);
  background: rgba(239, 95, 107, 0.08);
}

/* ============ 模态框 ============ */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(5, 7, 12, 0.7);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  z-index: 100;
  display: grid;
  place-items: center;
  padding: 20px;
}

.modal {
  background: linear-gradient(180deg, rgba(28, 33, 44, 0.95), rgba(22, 26, 35, 0.95));
  border: 1px solid var(--border-2);
  border-radius: var(--radius);
  width: 100%;
  max-width: 680px;
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.05) inset,
    0 32px 80px -20px rgba(0, 0, 0, 0.8);
  animation: modalIn 0.22s cubic-bezier(0.2, 0.8, 0.2, 1);
  overflow: hidden;
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.98);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--border);
}

.modal-head h3 {
  font-size: 15px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 0.3px;
}

.modal-tabs {
  display: flex;
  gap: 4px;
  padding: 12px 20px 0;
}

.modal-tab {
  background: transparent;
  border: 1px solid var(--border-2);
  color: var(--text-2);
  padding: 7px 14px;
  font-size: 12.5px;
  font-family: inherit;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  font-weight: 500;
}

.modal-tab:hover:not(.active) {
  color: var(--text);
  border-color: var(--accent);
  background: rgba(107, 140, 255, 0.06);
}

.modal-tab.active {
  background: linear-gradient(135deg, rgba(107, 140, 255, 0.9), rgba(143, 107, 255, 0.9));
  color: #fff;
  border-color: transparent;
  box-shadow: 0 4px 14px -4px var(--accent-glow);
  font-weight: 600;
}

.modal-body {
  padding: 14px 20px;
  overflow: auto;
  flex: 1;
  min-height: 0;
}

.modal-foot {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px 18px;
  border-top: 1px solid var(--border);
}

.code-block {
  margin: 0;
  padding: 14px 16px;
  background: rgba(8, 10, 15, 0.9);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: auto;
  max-height: 52vh;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12.5px;
  line-height: 1.65;
  color: #c8d0e0;
  white-space: pre;
  tab-size: 2;
}

.code-block code {
  font-family: inherit;
}

.import-tip {
  font-size: 12.5px;
  color: var(--text-2);
  margin-bottom: 12px;
  line-height: 1.55;
}

.import-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.import-textarea {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12.5px;
  line-height: 1.6;
  min-height: 220px;
  white-space: pre;
  overflow: auto;
}
</style>