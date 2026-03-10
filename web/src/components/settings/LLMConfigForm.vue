<script setup>
import { ref, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()

const model = ref('')
const baseUrl = ref('')
const apiKey = ref('')
const showKey = ref(false)
const testResult = ref(null)
const testing = ref(false)
const saving = ref(false)
const saved = ref(false)

onMounted(async () => {
  await configStore.fetchConfig()
  if (configStore.config) {
    model.value = configStore.config.llm?.model || ''
    baseUrl.value = configStore.config.llm?.api_base_url || ''
  }
})

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    const data = { model: model.value, api_base_url: baseUrl.value }
    if (apiKey.value) data.api_key = apiKey.value
    testResult.value = await configStore.testLLMConnection(data)
  } catch (e) {
    testResult.value = { success: false, error: e.message }
  } finally {
    testing.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const data = {
      llm: { model: model.value, api_base_url: baseUrl.value },
    }
    if (apiKey.value) data.llm.api_key = apiKey.value
    await configStore.saveConfig(data)
    saved.value = true
    setTimeout(() => saved.value = false, 2000)
  } catch (e) {
    alert('Save failed: ' + e.message)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="llm-config">
    <h3 class="llm-config__title">LLM Configuration</h3>

    <div class="llm-config__field">
      <label>Model Name</label>
      <input v-model="model" type="text" placeholder="deepseek-chat" />
    </div>

    <div class="llm-config__field">
      <label>API Base URL</label>
      <input v-model="baseUrl" type="url" placeholder="https://api.deepseek.com" />
    </div>

    <div class="llm-config__field">
      <label>API Key {{ configStore.config?.llm?.api_key_set ? `(current: ${configStore.config.llm.api_key_preview})` : '' }}</label>
      <div class="llm-config__key-row">
        <input
          v-model="apiKey"
          :type="showKey ? 'text' : 'password'"
          placeholder="Leave blank to keep current key"
        />
        <button class="llm-config__eye" @click="showKey = !showKey">{{ showKey ? '🙈' : '👁️' }}</button>
      </div>
    </div>

    <div class="llm-config__actions">
      <button
        class="llm-config__btn llm-config__btn--test"
        :disabled="testing"
        @click="testConnection"
      >
        {{ testing ? 'Testing...' : '🔌 Test Connection' }}
      </button>

      <button
        class="llm-config__btn llm-config__btn--save"
        :disabled="saving"
        @click="save"
      >
        {{ saved ? '✓ Saved!' : saving ? 'Saving...' : '💾 Save' }}
      </button>
    </div>

    <div v-if="testResult" class="llm-config__result" :class="testResult.success ? 'llm-config__result--ok' : 'llm-config__result--fail'">
      <template v-if="testResult.success">
        ✅ Connected! Latency: {{ testResult.latency_ms }}ms
      </template>
      <template v-else>
        ❌ {{ testResult.error }}
      </template>
    </div>
  </div>
</template>

<style scoped>
.llm-config {
  max-width: 500px;
}

.llm-config__title {
  font-size: var(--text-lg);
  font-weight: 600;
  margin-bottom: var(--space-lg);
}

.llm-config__field {
  margin-bottom: var(--space-md);
}

.llm-config__field label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.llm-config__field input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color var(--transition-fast);
}

.llm-config__field input:focus {
  border-color: var(--color-accent);
}

.llm-config__key-row {
  display: flex;
  gap: var(--space-sm);
}

.llm-config__key-row input {
  flex: 1;
}

.llm-config__eye {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
}

.llm-config__actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
}

.llm-config__btn {
  padding: 8px 16px;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: 500;
  transition: all var(--transition-fast);
}

.llm-config__btn--test {
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  background: var(--color-bg-primary);
}

.llm-config__btn--test:hover:not(:disabled) {
  background: var(--color-bg-tertiary);
}

.llm-config__btn--save {
  background: var(--color-accent);
  color: white;
}

.llm-config__btn--save:hover:not(:disabled) {
  background: var(--color-accent-hover);
}

.llm-config__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.llm-config__result {
  margin-top: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
}

.llm-config__result--ok {
  background: #ecfdf5;
  color: #065f46;
}

.llm-config__result--fail {
  background: #fef2f2;
  color: #991b1b;
}
</style>
