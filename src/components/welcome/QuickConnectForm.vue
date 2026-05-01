<script setup lang="ts">
import { ref } from 'vue';
import type { QuickConnectReq } from '@/types/connection';

const emit = defineEmits<{
  (e: 'connect', config: QuickConnectReq): void;
  (e: 'test', config: QuickConnectReq): void;
}>();

const host = ref('127.0.0.1');
const port = ref(6379);
const password = ref('');
const loading = ref(false);
const testing = ref(false);
const errorMsg = ref('');
const testResult = ref('');

function getConfig(): QuickConnectReq {
  return {
    host: host.value,
    port: port.value,
    password: password.value || undefined,
    timeout_ms: 5000,
  };
}

function handleConnect() {
  errorMsg.value = '';
  testResult.value = '';
  loading.value = true;
  emit('connect', getConfig());
}

function handleTest() {
  errorMsg.value = '';
  testResult.value = '';
  testing.value = true;
  emit('test', getConfig());
}

// Exposed methods for parent to control state
function setLoading(val: boolean) { loading.value = val; }
function setTesting(val: boolean) { testing.value = val; }
function setError(msg: string) { errorMsg.value = msg; loading.value = false; testing.value = false; }
function setTestResult(msg: string) { testResult.value = msg; testing.value = false; }

defineExpose({ setLoading, setTesting, setError, setTestResult });
</script>

<template>
  <div class="quick-connect-form">
    <h3 class="form-title">
      <i class="ri-flashlight-line" />
      快速连接
    </h3>

    <div class="form-row">
      <div class="form-group flex-1">
        <label>主机</label>
        <input
          v-model="host"
          type="text"
          placeholder="127.0.0.1"
          :disabled="loading"
          @keyup.enter="handleConnect"
        />
      </div>
      <div class="form-group port-group">
        <label>端口</label>
        <input
          v-model.number="port"
          type="number"
          placeholder="6379"
          :disabled="loading"
          @keyup.enter="handleConnect"
        />
      </div>
    </div>

    <div class="form-row">
      <div class="form-group flex-1">
        <label>密码 <span class="optional">(可选)</span></label>
        <input
          v-model="password"
          type="password"
          placeholder="输入密码..."
          :disabled="loading"
          @keyup.enter="handleConnect"
        />
      </div>
    </div>

    <!-- Connect button (primary) -->
    <button
      class="connect-btn"
      :class="{ loading }"
      :disabled="loading || testing"
      @click="handleConnect"
    >
      <i v-if="!loading" class="ri-link" />
      <i v-else class="ri-loader-4-line spin" />
      {{ loading ? '连接中...' : '连接' }}
    </button>

    <!-- Test connection (secondary) -->
    <button
      class="test-link"
      :disabled="loading || testing"
      @click="handleTest"
    >
      <i v-if="!testing" class="ri-wifi-line" />
      <i v-else class="ri-loader-4-line spin" />
      {{ testing ? '测试中...' : '测试连接' }}
    </button>

    <!-- Error message -->
    <Transition name="fade">
      <div v-if="errorMsg" class="result-toast error">
        <i class="ri-close-circle-fill" />
        <span>{{ errorMsg }}</span>
      </div>
    </Transition>

    <!-- Test result -->
    <Transition name="fade">
      <div v-if="testResult" class="result-toast success">
        <i class="ri-checkbox-circle-fill" />
        <span>{{ testResult }}</span>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.quick-connect-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--srn-color-text-2);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.form-row { display: flex; gap: 10px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.flex-1 { flex: 1; }
.port-group { width: 100px; }

.form-group label {
  font-size: 11px;
  font-weight: 500;
  color: var(--srn-color-text-2);
}
.optional { font-weight: 400; color: var(--srn-color-text-3); }

.form-group input {
  height: 34px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 10px;
  font-size: 13px;
  font-family: var(--srn-font-mono);
  background: var(--srn-color-surface-1);
  color: var(--srn-color-text-1);
  outline: none;
  transition: border-color var(--srn-motion-fast);
}
.form-group input:focus {
  border-color: var(--srn-color-info);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}
.form-group input:disabled { opacity: 0.6; }

.connect-btn {
  width: 100%;
  height: 38px;
  border: none;
  border-radius: var(--srn-radius-sm);
  background: linear-gradient(135deg, var(--srn-color-primary), var(--srn-color-primary-light));
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all var(--srn-motion-fast);
}
.connect-btn:hover:not(:disabled) {
  opacity: 0.9;
  box-shadow: 0 4px 12px rgba(220, 56, 45, 0.3);
}
.connect-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.test-link {
  width: 100%;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--srn-color-text-3);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: color var(--srn-motion-fast);
}
.test-link:hover:not(:disabled) { color: var(--srn-color-info); }
.test-link:disabled { opacity: 0.5; cursor: not-allowed; }

.result-toast {
  padding: 10px 14px;
  border-radius: var(--srn-radius-sm);
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.result-toast.success {
  background: rgba(52, 199, 89, 0.08);
  color: #166534;
  border: 1px solid rgba(52, 199, 89, 0.2);
}
.result-toast.error {
  background: rgba(255, 59, 48, 0.08);
  color: #9f1239;
  border: 1px solid rgba(255, 59, 48, 0.2);
}

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }

.fade-enter-active, .fade-leave-active { transition: all var(--srn-motion-normal); }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
