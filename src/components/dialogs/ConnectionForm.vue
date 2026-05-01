<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import type { ConnectionConfig, SshConfig, TlsConfig, ConnectionType } from '@/types/connection';
import { connectionTest, connectionTestSsh, connectionTestTls, connectionTestSentinel, connectionTestCluster } from '@/ipc/connection';
import { useConnectionStore } from '@/stores/connection';
import type { IpcError } from '@/types/ipc';
import { getFriendlyMessage } from '@/ipc';

const props = defineProps<{
  visible: boolean;
  editConfig?: ConnectionConfig | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'saved', id: string): void;
}>();

const connStore = useConnectionStore();

const defaultSshConfig = (): SshConfig => ({
  host: '',
  port: 22,
  username: '',
  auth_method: 'password',
  password: '',
  private_key_path: null,
  private_key_passphrase: null,
  timeout_ms: 10000,
});

const defaultTlsConfig = (): TlsConfig => ({
  verify_cert: true,
  ca_cert_path: null,
  client_cert_path: null,
  client_key_path: null,
  min_tls_version: null,
  server_name: null,
});

const form = ref<ConnectionConfig>({
  id: '',
  name: '',
  group_name: '',
  host: '127.0.0.1',
  port: 6379,
  password: '',
  auth_db: 0,
  timeout_ms: 5000,
  sort_order: 0,
  connection_type: 'tcp',
  ssh_config: null,
  tls_config: null,
  sentinel_nodes: null,
  master_name: null,
  cluster_nodes: null,
});

const testResult = ref('');
const testType = ref<'success' | 'error' | ''>('');
const testing = ref(false);
const saving = ref(false);
const testDetails = ref<string[]>([]);

const isSsh = computed(() => form.value.connection_type === 'ssh');
const isTls = computed(() => form.value.connection_type === 'tls');
const isSentinel = computed(() => form.value.connection_type === 'sentinel');
const isCluster = computed(() => form.value.connection_type === 'cluster');

// Fill form when editing
watch(() => props.editConfig, (cfg) => {
  if (cfg) {
    form.value = {
      ...cfg,
      password: '',
      connection_type: cfg.connection_type ?? 'tcp',
      ssh_config: cfg.ssh_config ? { ...cfg.ssh_config, password: '' } : null,
      tls_config: cfg.tls_config ?? null,
      sentinel_nodes: cfg.sentinel_nodes ? [...cfg.sentinel_nodes] : null,
      master_name: cfg.master_name ?? null,
      cluster_nodes: cfg.cluster_nodes ? [...cfg.cluster_nodes] : null,
    };
  } else {
    resetForm();
  }
}, { immediate: true });

// Initialize SSH/TLS/Sentinel/Cluster config when type changes
watch(() => form.value.connection_type, (type) => {
  if (type === 'ssh' && !form.value.ssh_config) {
    form.value.ssh_config = defaultSshConfig();
  }
  if (type === 'tls' && !form.value.tls_config) {
    form.value.tls_config = defaultTlsConfig();
  }
  if (type === 'sentinel' && !form.value.sentinel_nodes) {
    form.value.sentinel_nodes = [''];
    form.value.master_name = 'mymaster';
  }
  if (type === 'cluster' && !form.value.cluster_nodes) {
    form.value.cluster_nodes = [''];
  }
});

function resetForm() {
  form.value = {
    id: '',
    name: '',
    group_name: '',
    host: '127.0.0.1',
    port: 6379,
    password: '',
    auth_db: 0,
    timeout_ms: 5000,
    sort_order: 0,
    connection_type: 'tcp',
    ssh_config: null,
    tls_config: null,
    sentinel_nodes: null,
    master_name: null,
    cluster_nodes: null,
  };
  testResult.value = '';
  testType.value = '';
  testDetails.value = [];
}

async function handleTest() {
  testing.value = true;
  testResult.value = '';
  testType.value = '';
  testDetails.value = [];
  try {
    if (form.value.connection_type === 'ssh') {
      const res = await connectionTestSsh(form.value);
      testDetails.value = res.details;
      if (res.success) {
        testType.value = 'success';
        testResult.value = `✓ SSH 隧道连接成功！延迟 ${res.latency_ms}ms`;
      } else {
        testType.value = 'error';
        testResult.value = `✗ ${res.error ?? 'SSH 连接失败'}`;
      }
    } else if (form.value.connection_type === 'tls') {
      const res = await connectionTestTls(form.value);
      testDetails.value = res.details;
      if (res.success) {
        testType.value = 'success';
        testResult.value = `✓ TLS 加密连接成功！延迟 ${res.latency_ms}ms`;
      } else {
        testType.value = 'error';
        testResult.value = `✗ ${res.error ?? 'TLS 连接失败'}`;
      }
    } else if (form.value.connection_type === 'sentinel') {
      const res = await connectionTestSentinel(form.value);
      testDetails.value = res.details;
      if (res.success) {
        testType.value = 'success';
        testResult.value = `✓ Sentinel 连接成功！延迟 ${res.latency_ms}ms`;
      } else {
        testType.value = 'error';
        testResult.value = `✗ ${res.error ?? 'Sentinel 连接失败'}`;
      }
    } else if (form.value.connection_type === 'cluster') {
      const res = await connectionTestCluster(form.value);
      testDetails.value = res.details;
      if (res.success) {
        testType.value = 'success';
        testResult.value = `✓ Cluster 连接成功！延迟 ${res.latency_ms}ms`;
      } else {
        testType.value = 'error';
        testResult.value = `✗ ${res.error ?? 'Cluster 连接失败'}`;
      }
    } else {
      const res = await connectionTest({
        host: form.value.host,
        port: form.value.port,
        password: form.value.password || undefined,
        timeout_ms: form.value.timeout_ms,
      });
      testType.value = 'success';
      testResult.value = `✓ 连接成功！延迟 ${res.latency_ms}ms${res.server_version ? ` · Redis ${res.server_version}` : ''}`;
    }
  } catch (e) {
    const err = e as IpcError;
    testType.value = 'error';
    testResult.value = `✗ ${getFriendlyMessage(err)}`;
  } finally {
    testing.value = false;
  }
}

async function handleSave() {
  // Validate required fields and show inline error
  if (!form.value.name) {
    testType.value = 'error';
    testResult.value = '✗ 请填写连接名称';
    return;
  }
  if (!form.value.host) {
    testType.value = 'error';
    testResult.value = '✗ 请填写主机地址';
    return;
  }

  saving.value = true;
  testResult.value = '';
  testType.value = '';
  try {
    const configToSave = { ...form.value };
    if (props.editConfig && !configToSave.password) {
      configToSave.password = null;
    }
    const id = await connStore.saveConnection(configToSave);
    emit('saved', id);
    emit('close');
  } catch (e) {
    const err = e as IpcError;
    testType.value = 'error';
    testResult.value = `✗ ${getFriendlyMessage(err)}`;
    return;
    saving.value = false;
  }
}

function handleClose() {
  emit('close');
}
</script>

<template>
  <Transition name="modal">
    <div v-if="visible" class="modal-overlay" @click.self="handleClose">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ editConfig ? '编辑连接' : '新建连接' }}</h3>
          <button class="close-btn" @click="handleClose"><i class="ri-close-line" /></button>
        </div>

        <div class="modal-body">
          <!-- Keychain notice -->
          <div class="keychain-notice">
            <i class="ri-shield-keyhole-line" />
            密码将安全存储于 macOS Keychain，首次保存时系统会弹出授权提示。
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label>连接名称 <span class="required">*</span></label>
              <input v-model="form.name" type="text" placeholder="例: 本地开发" />
            </div>
            <div class="form-group" style="width: 140px;">
              <label>分组</label>
              <input v-model="form.group_name" type="text" placeholder="例: 开发环境" />
            </div>
          </div>

          <!-- Connection type selector -->
          <div class="form-group">
            <label>连接类型</label>
            <div class="conn-type-tabs">
              <button
                v-for="t in (['tcp', 'ssh', 'tls', 'sentinel', 'cluster'] as ConnectionType[])"
                :key="t"
                class="conn-type-tab"
                :class="{ active: form.connection_type === t }"
                @click="form.connection_type = t"
              >
                <i :class="t === 'tcp' ? 'ri-server-line' : t === 'ssh' ? 'ri-terminal-box-line' : t === 'tls' ? 'ri-lock-line' : t === 'sentinel' ? 'ri-shield-check-line' : 'ri-grid-line'" />
                {{ t === 'sentinel' ? 'SENTINEL' : t === 'cluster' ? 'CLUSTER' : t.toUpperCase() }}
              </button>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label>{{ isSsh ? 'Redis 主机（内网）' : '主机' }} <span class="required">*</span></label>
              <input v-model="form.host" type="text" placeholder="127.0.0.1" />
            </div>
            <div class="form-group" style="width: 100px;">
              <label>Redis 端口</label>
              <input v-model.number="form.port" type="number" placeholder="6379" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label>Redis 密码</label>
              <input
                v-model="form.password"
                type="password"
                :placeholder="editConfig?.has_password ? '留空保持原密码（Touch ID 保护）' : '可选'"
              />
            </div>
            <div class="form-group" style="width: 80px;">
              <label>默认 DB</label>
              <input v-model.number="form.auth_db" type="number" min="0" max="15" placeholder="0" />
            </div>
            <div class="form-group" style="width: 100px;">
              <label>超时 (ms)</label>
              <input v-model.number="form.timeout_ms" type="number" placeholder="5000" />
            </div>
          </div>

          <!-- SSH Configuration -->
          <template v-if="isSsh && form.ssh_config">
            <div class="section-divider">
              <i class="ri-terminal-box-line" />
              SSH 隧道配置
            </div>

            <div class="form-row">
              <div class="form-group flex-1">
                <label>SSH 主机 <span class="required">*</span></label>
                <input v-model="form.ssh_config.host" type="text" placeholder="跳板机地址" />
              </div>
              <div class="form-group" style="width: 80px;">
                <label>SSH 端口</label>
                <input v-model.number="form.ssh_config.port" type="number" placeholder="22" />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group flex-1">
                <label>SSH 用户名 <span class="required">*</span></label>
                <input v-model="form.ssh_config.username" type="text" placeholder="ubuntu" />
              </div>
              <div class="form-group" style="width: 140px;">
                <label>认证方式</label>
                <select v-model="form.ssh_config.auth_method" class="form-select">
                  <option value="password">密码</option>
                  <option value="private_key">私钥</option>
                </select>
              </div>
            </div>

            <div v-if="form.ssh_config.auth_method === 'password'" class="form-group">
              <label>SSH 密码</label>
              <input v-model="form.ssh_config.password" type="password" placeholder="SSH 登录密码" />
            </div>

            <template v-else>
              <div class="form-group">
                <label>私钥文件路径 <span class="required">*</span></label>
                <input v-model="form.ssh_config.private_key_path" type="text" placeholder="~/.ssh/id_rsa" />
              </div>
              <div class="form-group">
                <label>私钥密码（可选）</label>
                <input v-model="form.ssh_config.private_key_passphrase" type="password" placeholder="私钥加密密码" />
              </div>
            </template>
          </template>

          <!-- TLS Configuration -->
          <template v-if="isTls && form.tls_config">
            <div class="section-divider">
              <i class="ri-lock-line" />
              TLS 加密配置
            </div>

            <div class="form-row">
              <div class="form-group flex-1">
                <label>服务器名称（SNI）</label>
                <input v-model="form.tls_config.server_name" type="text" placeholder="留空使用主机名" />
              </div>
              <div class="form-group" style="width: 120px;">
                <label>最低 TLS 版本</label>
                <select v-model="form.tls_config.min_tls_version" class="form-select">
                  <option :value="null">自动</option>
                  <option value="tls1.2">TLS 1.2</option>
                  <option value="tls1.3">TLS 1.3</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label class="checkbox-label">
                <input v-model="form.tls_config.verify_cert" type="checkbox" />
                验证服务器证书（生产环境建议开启）
              </label>
            </div>

            <div v-if="!form.tls_config.verify_cert" class="warning-notice">
              <i class="ri-alert-line" />
              已禁用证书验证，存在安全风险，请仅在测试环境使用。
            </div>

            <div class="form-group">
              <label>CA 证书路径（可选）</label>
              <input v-model="form.tls_config.ca_cert_path" type="text" placeholder="/path/to/ca.pem" />
            </div>

            <div class="form-row">
              <div class="form-group flex-1">
                <label>客户端证书（可选）</label>
                <input v-model="form.tls_config.client_cert_path" type="text" placeholder="/path/to/client.crt" />
              </div>
              <div class="form-group flex-1">
                <label>客户端私钥（可选）</label>
                <input v-model="form.tls_config.client_key_path" type="text" placeholder="/path/to/client.key" />
              </div>
            </div>
          </template>

          <!-- Sentinel Configuration -->
          <template v-if="isSentinel">
            <div class="section-divider">
              <i class="ri-shield-check-line" />
              Sentinel 高可用配置
            </div>

            <div class="form-group">
              <label>Master 名称 <span class="required">*</span></label>
              <input v-model="form.master_name" type="text" placeholder="mymaster" />
            </div>

            <div class="form-group">
              <label>
                Sentinel 节点列表 <span class="required">*</span>
                <button class="add-node-btn" @click="form.sentinel_nodes?.push('')">+ 添加节点</button>
              </label>
              <div v-for="(_, idx) in form.sentinel_nodes" :key="idx" class="node-row">
                <input
                  v-model="form.sentinel_nodes![idx]"
                  type="text"
                  placeholder="host:port（例: 10.0.0.1:26379）"
                  class="flex-1"
                />
                <button
                  v-if="(form.sentinel_nodes?.length ?? 0) > 1"
                  class="remove-node-btn"
                  @click="form.sentinel_nodes?.splice(idx, 1)"
                >
                  <i class="ri-delete-bin-line" />
                </button>
              </div>
            </div>

            <div class="info-notice">
              <i class="ri-information-line" />
              Sentinel 模式将自动发现 master 节点，无需手动指定 Redis 主机地址。如果 master 故障，Sentinel 会自动切换。
            </div>
          </template>

          <!-- Cluster Configuration -->
          <template v-if="isCluster">
            <div class="section-divider">
              <i class="ri-grid-line" />
              Cluster 集群配置
            </div>

            <div class="form-group">
              <label>
                Seed 节点列表 <span class="required">*</span>
                <button class="add-node-btn" @click="form.cluster_nodes?.push('')">+ 添加节点</button>
              </label>
              <div v-for="(_, idx) in form.cluster_nodes" :key="idx" class="node-row">
                <input
                  v-model="form.cluster_nodes![idx]"
                  type="text"
                  placeholder="host:port（例: 10.0.0.1:6379）"
                  class="flex-1"
                />
                <button
                  v-if="(form.cluster_nodes?.length ?? 0) > 1"
                  class="remove-node-btn"
                  @click="form.cluster_nodes?.splice(idx, 1)"
                >
                  <i class="ri-delete-bin-line" />
                </button>
              </div>
            </div>

            <div class="info-notice">
              <i class="ri-information-line" />
              Cluster 模式只需提供部分 seed 节点，客户端会自动发现完整拓扑（所有 master/slave 节点）。
            </div>
          </template>

          <!-- Test result -->
          <Transition name="fade">
            <div v-if="testResult" class="test-result" :class="testType">
              {{ testResult }}
              <ul v-if="testDetails.length" class="test-details">
                <li v-for="(d, i) in testDetails" :key="i">{{ d }}</li>
              </ul>
            </div>
          </Transition>
        </div>

        <div class="modal-footer">
          <button class="btn-test" :disabled="testing" @click="handleTest">
            <i v-if="!testing" class="ri-wifi-line" />
            <i v-else class="ri-loader-4-line spin" />
            {{ testing ? '测试中...' : '测试连接' }}
          </button>
          <div class="footer-right">
            <button class="btn-cancel" @click="handleClose">取消</button>
            <button class="btn-save" :disabled="saving || !form.name || !form.host" @click="handleSave">
              <i v-if="!saving" class="ri-save-line" />
              <i v-else class="ri-loader-4-line spin" />
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  width: 520px;
  max-height: 90vh;
  overflow-y: auto;
  background: var(--srn-color-surface-2);
  border-radius: var(--srn-radius-lg);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border: 1px solid var(--srn-color-border);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--srn-color-border);
}

.modal-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--srn-color-text-1);
}

.close-btn {
  border: none;
  background: transparent;
  color: var(--srn-color-text-3);
  cursor: pointer;
  font-size: 18px;
  padding: 2px;
  border-radius: var(--srn-radius-xs);
}
.close-btn:hover { color: var(--srn-color-text-1); background: rgba(0,0,0,0.06); }

.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }

.keychain-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(0, 122, 255, 0.06);
  border: 1px solid rgba(0, 122, 255, 0.15);
  border-radius: var(--srn-radius-sm);
  font-size: 11px;
  color: var(--srn-color-info);
}

/* Connection type tabs */
.conn-type-tabs {
  display: flex;
  gap: 6px;
}

.conn-type-tab {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  background: var(--srn-color-surface-1);
  color: var(--srn-color-text-2);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--srn-motion-fast);
}
.conn-type-tab:hover { border-color: var(--srn-color-info); color: var(--srn-color-info); }
.conn-type-tab.active {
  border-color: var(--srn-color-primary);
  background: rgba(0, 122, 255, 0.08);
  color: var(--srn-color-primary);
}

/* Section divider */
.section-divider {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--srn-color-text-2);
  padding: 4px 0;
  border-bottom: 1px solid var(--srn-color-border);
  margin-top: 4px;
}

.form-row { display: flex; gap: 10px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.flex-1 { flex: 1; }

.form-group label {
  font-size: 11px;
  font-weight: 500;
  color: var(--srn-color-text-2);
}

.required { color: var(--srn-color-primary); }

.form-group input, .form-select {
  height: 32px;
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
.form-group input:focus, .form-select:focus { border-color: var(--srn-color-info); }

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--srn-color-text-2);
  cursor: pointer;
}
.checkbox-label input[type="checkbox"] { width: 14px; height: 14px; cursor: pointer; }

.warning-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 149, 0, 0.08);
  border: 1px solid rgba(255, 149, 0, 0.2);
  border-radius: var(--srn-radius-sm);
  font-size: 11px;
  color: #92400e;
}

.info-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(0, 122, 255, 0.06);
  border: 1px solid rgba(0, 122, 255, 0.15);
  border-radius: var(--srn-radius-sm);
  font-size: 11px;
  color: var(--srn-color-info);
}

.node-row {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-bottom: 4px;
}

.node-row input {
  height: 32px;
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
.node-row input:focus { border-color: var(--srn-color-info); }

.add-node-btn {
  border: none;
  background: none;
  color: var(--srn-color-info);
  font-size: 11px;
  cursor: pointer;
  padding: 2px 6px;
  margin-left: 8px;
}
.add-node-btn:hover { text-decoration: underline; }

.remove-node-btn {
  border: none;
  background: none;
  color: var(--srn-color-text-3);
  cursor: pointer;
  font-size: 14px;
  padding: 4px;
  border-radius: var(--srn-radius-xs);
}
.remove-node-btn:hover { color: #ef4444; background: rgba(239, 68, 68, 0.08); }

.test-result {
  padding: 8px 12px;
  border-radius: var(--srn-radius-sm);
  font-size: 12px;
}
.test-result.success { background: rgba(52,199,89,0.08); color: #166534; border: 1px solid rgba(52,199,89,0.2); }
.test-result.error { background: rgba(255,59,48,0.08); color: #9f1239; border: 1px solid rgba(255,59,48,0.2); }

.test-details {
  margin: 6px 0 0 0;
  padding-left: 16px;
  font-size: 11px;
  opacity: 0.8;
}
.test-details li { margin: 2px 0; }

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-top: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-1);
}

.footer-right { display: flex; gap: 8px; }

.btn-test, .btn-cancel, .btn-save {
  height: 32px;
  padding: 0 14px;
  border-radius: var(--srn-radius-sm);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all var(--srn-motion-fast);
}

.btn-test {
  border: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
  color: var(--srn-color-text-2);
}
.btn-test:hover:not(:disabled) { border-color: var(--srn-color-info); color: var(--srn-color-info); }

.btn-cancel {
  border: 1px solid var(--srn-color-border);
  background: transparent;
  color: var(--srn-color-text-2);
}
.btn-cancel:hover { background: rgba(0,0,0,0.04); }

.btn-save {
  border: none;
  background: var(--srn-color-primary);
  color: #fff;
}
.btn-save:hover:not(:disabled) { opacity: 0.9; }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }

.modal-enter-active, .modal-leave-active { transition: all 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-card, .modal-leave-to .modal-card { transform: scale(0.95); }

.fade-enter-active, .fade-leave-active { transition: all 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
