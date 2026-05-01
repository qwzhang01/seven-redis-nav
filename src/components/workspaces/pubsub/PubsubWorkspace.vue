<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { usePubSubStore } from '@/stores/pubsub';
import { useConnectionStore } from '@/stores/connection';
import { pubsubSubscribe, pubsubUnsubscribe, pubsubPublish } from '@/ipc/phase2';
import { configSet } from '@/ipc/phase2';
import { listenPubSubMessage } from '@/ipc/event';

const store = usePubSubStore();
const connStore = useConnectionStore();

const channelInput = ref('');
const isPattern = ref(false);
const subscribing = ref(false);
const streamRef = ref<HTMLDivElement | null>(null);

// Publish form
const publishChannel = ref('');
const publishMessage = ref('');
const publishing = ref(false);

// Timed repeat publish
const repeatEnabled = ref(false);
const repeatInterval = ref(1); // seconds
const repeatCount = ref(0);
const repeatMax = ref(0); // 0 = unlimited
let repeatTimer: ReturnType<typeof setInterval> | null = null;

// Channel pause/resume state
const pausedChannels = ref<Set<string>>(new Set());

// Export dialog
const showExportDialog = ref(false);
const exportFormat = ref<'json' | 'ndjson'>('json');
const exportScope = ref<'all' | 'filtered' | 'channel'>('all');
const exportChannel = ref('');

// Keyspace notify presets
const showNotifyPresets = ref(false);
const notifyLoading = ref(false);

let unlistenMsg: (() => void) | null = null;

onMounted(async () => {
  unlistenMsg = await listenPubSubMessage((msg) => {
    // Skip if channel is paused
    if (pausedChannels.value.has(msg.channel)) return;
    store.addMessage(msg);
    // Auto-scroll if not paused
    if (!store.paused && streamRef.value) {
      requestAnimationFrame(() => {
        if (streamRef.value) {
          streamRef.value.scrollTop = streamRef.value.scrollHeight;
        }
      });
    }
  });
});

onUnmounted(() => {
  unlistenMsg?.();
  stopRepeat();
});

async function handleSubscribe() {
  const raw = channelInput.value.trim();
  if (!raw || !connStore.activeConnId) return;

  const channels = raw.split(',').map((s) => s.trim()).filter(Boolean);
  subscribing.value = true;
  try {
    await pubsubSubscribe(connStore.activeConnId, channels, isPattern.value);
    store.addSubscription(channels, isPattern.value);
    channelInput.value = '';
  } catch (e) {
    console.error('Subscribe failed:', e);
  } finally {
    subscribing.value = false;
  }
}

async function handleUnsubscribe(channel: string, pattern: boolean) {
  if (!connStore.activeConnId) return;
  try {
    await pubsubUnsubscribe(connStore.activeConnId, [channel], pattern);
    store.removeSubscription([channel], pattern);
    pausedChannels.value.delete(channel);
  } catch (e) {
    console.error('Unsubscribe failed:', e);
  }
}

async function handleUnsubscribeAll() {
  if (!connStore.activeConnId) return;
  try {
    if (store.subscriptions.length > 0) {
      await pubsubUnsubscribe(connStore.activeConnId, store.subscriptions, false);
    }
    if (store.patternSubscriptions.length > 0) {
      await pubsubUnsubscribe(connStore.activeConnId, store.patternSubscriptions, true);
    }
    store.reset();
    pausedChannels.value.clear();
  } catch (e) {
    console.error('Unsubscribe all failed:', e);
  }
}

async function handlePublish() {
  if (!publishChannel.value.trim() || !publishMessage.value.trim() || !connStore.activeConnId) return;
  publishing.value = true;
  try {
    await pubsubPublish(connStore.activeConnId, publishChannel.value.trim(), publishMessage.value.trim());
    store.addMessage({
      channel: publishChannel.value.trim(),
      pattern: null,
      message: publishMessage.value.trim(),
      timestamp: new Date().toISOString(),
    });
    if (!repeatEnabled.value) {
      publishMessage.value = '';
    }
  } catch (e) {
    console.error('Publish failed:', e);
  } finally {
    publishing.value = false;
  }
}

// Timed repeat publish
function startRepeat() {
  if (repeatTimer) return;
  repeatEnabled.value = true;
  repeatCount.value = 0;
  repeatTimer = setInterval(async () => {
    if (repeatMax.value > 0 && repeatCount.value >= repeatMax.value) {
      stopRepeat();
      return;
    }
    // Rate limit: max 10/sec
    if (repeatInterval.value < 0.1) {
      repeatInterval.value = 0.1;
    }
    await handlePublish();
    repeatCount.value++;
  }, repeatInterval.value * 1000);
}

function stopRepeat() {
  repeatEnabled.value = false;
  if (repeatTimer) {
    clearInterval(repeatTimer);
    repeatTimer = null;
  }
}

// Channel pause/resume
function toggleChannelPause(channel: string) {
  if (pausedChannels.value.has(channel)) {
    pausedChannels.value.delete(channel);
  } else {
    pausedChannels.value.add(channel);
  }
}

function isChannelPaused(channel: string): boolean {
  return pausedChannels.value.has(channel);
}

// Message export
function openExportDialog() {
  exportChannel.value = '';
  showExportDialog.value = true;
}

function getExportData(): string {
  let messages = store.messages;
  if (exportScope.value === 'filtered') {
    messages = store.filteredMessages;
  } else if (exportScope.value === 'channel' && exportChannel.value) {
    messages = messages.filter(m => m.channel === exportChannel.value);
  }

  if (exportFormat.value === 'json') {
    return JSON.stringify(messages, null, 2);
  } else {
    return messages.map(m => JSON.stringify(m)).join('\n');
  }
}

async function handleExport() {
  try {
    const data = getExportData();
    const ext = exportFormat.value === 'json' ? 'json' : 'ndjson';
    const blob = new Blob([data], { type: ext === 'json' ? 'application/json' : 'application/x-ndjson' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pubsub-messages.${ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showExportDialog.value = false;
  } catch (e: any) {
    console.error('Export failed:', e);
  }
}

// Keyspace notification presets
async function applyNotifyPreset(flags: string) {
  if (!connStore.activeConnId) return;
  notifyLoading.value = true;
  try {
    // Set notify-keyspace-events
    await configSet(connStore.activeConnId, 'notify-keyspace-events', flags);
    // Subscribe to corresponding patterns
    const patterns: string[] = [];
    if (flags.includes('K')) {
      // Keyspace notifications: __keyspace@0__:<key>
      patterns.push('__keyspace@0__:*');
    }
    if (flags.includes('E')) {
      // Keyevent notifications: __keyevent@0__:<event>
      patterns.push('__keyevent@0__:*');
    }
    if (patterns.length > 0) {
      await pubsubSubscribe(connStore.activeConnId, patterns, true);
      store.addSubscription(patterns, true);
    }
    showNotifyPresets.value = false;
  } catch (e: any) {
    console.error('Failed to apply notify preset:', e);
  } finally {
    notifyLoading.value = false;
  }
}

function formatTime(ts: string) {
  try {
    const d = new Date(ts);
    const time = d.toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const ms = String(d.getMilliseconds()).padStart(3, '0');
    return `${time}.${ms}`;
  } catch {
    return ts;
  }
}
</script>

<template>
  <div class="pubsub-workspace">
    <!-- Top bar: subscribe input -->
    <div class="pubsub-toolbar">
      <div class="subscribe-form">
        <input
          v-model="channelInput"
          type="text"
          class="channel-input"
          placeholder="Channel name (comma-separated)..."
          :disabled="subscribing"
          @keydown.enter="handleSubscribe"
        />
        <label class="pattern-toggle">
          <input v-model="isPattern" type="checkbox" />
          <span>Pattern</span>
        </label>
        <button class="btn-subscribe" :disabled="!channelInput.trim() || subscribing" @click="handleSubscribe">
          <i class="ri-add-line" /> Subscribe
        </button>
      </div>
      <div class="toolbar-actions">
        <button v-if="store.hasSubscriptions" class="btn-icon" title="Unsubscribe All" @click="handleUnsubscribeAll">
          <i class="ri-close-circle-line" />
        </button>
        <button class="btn-icon" :class="{ active: store.paused }" :title="store.paused ? 'Resume' : 'Pause'" @click="store.paused ? store.resume() : store.pause()">
          <i :class="store.paused ? 'ri-play-line' : 'ri-pause-line'" />
        </button>
        <button class="btn-icon" title="Clear" @click="store.clearMessages">
          <i class="ri-delete-bin-line" />
        </button>
      </div>
    </div>

    <!-- Active subscriptions -->
    <div v-if="store.hasSubscriptions" class="subscriptions-bar">
      <span class="sub-label">Subscriptions:</span>
      <span v-for="ch in store.subscriptions" :key="'ch-' + ch" class="sub-tag" :class="{ paused: isChannelPaused(ch) }">
        {{ ch }}
        <button class="sub-pause-btn" :title="isChannelPaused(ch) ? '恢复' : '暂停'" @click="toggleChannelPause(ch)">
          <i :class="isChannelPaused(ch) ? 'ri-play-line' : 'ri-pause-line'" />
        </button>
        <i class="ri-close-line" @click="handleUnsubscribe(ch, false)" />
      </span>
      <span v-for="pat in store.patternSubscriptions" :key="'pat-' + pat" class="sub-tag pattern" :class="{ paused: isChannelPaused(pat) }">
        {{ pat }} <small>(pattern)</small>
        <button class="sub-pause-btn" :title="isChannelPaused(pat) ? '恢复' : '暂停'" @click="toggleChannelPause(pat)">
          <i :class="isChannelPaused(pat) ? 'ri-play-line' : 'ri-pause-line'" />
        </button>
        <i class="ri-close-line" @click="handleUnsubscribe(pat, true)" />
      </span>
    </div>

    <!-- Publish form -->
    <div class="publish-bar">
      <span class="pub-label">PUBLISH</span>
      <input
        v-model="publishChannel"
        type="text"
        class="pub-channel-input"
        placeholder="Channel"
        @keydown.enter="handlePublish"
      />
      <input
        v-model="publishMessage"
        type="text"
        class="pub-msg-input"
        placeholder="Message"
        @keydown.enter="handlePublish"
      />
      <button class="btn-publish" :disabled="!publishChannel.trim() || !publishMessage.trim() || publishing" @click="handlePublish">
        <i class="ri-send-plane-line" /> Send
      </button>
      <!-- Timed repeat controls -->
      <div class="repeat-controls">
        <label class="repeat-toggle" title="定时重复发送">
          <input v-model="repeatEnabled" type="checkbox" @change="(e: Event) => { if ((e.target as HTMLInputElement).checked) startRepeat(); else stopRepeat(); }" />
          <i class="ri-timer-line" />
        </label>
        <template v-if="repeatEnabled">
          <input
            v-model.number="repeatInterval"
            type="number"
            class="repeat-interval"
            min="0.1"
            step="0.1"
            title="发送间隔（秒）"
          />
          <span class="repeat-unit">s</span>
          <input
            v-model.number="repeatMax"
            type="number"
            class="repeat-max"
            min="0"
            step="1"
            placeholder="∞"
            title="最大次数（0=无限）"
          />
          <span class="repeat-count" :title="`已发送 ${repeatCount} 次`">{{ repeatCount }}</span>
          <button class="btn-sm-repeat" :class="{ active: repeatTimer }" @click="repeatTimer ? stopRepeat() : startRepeat()">
            <i :class="repeatTimer ? 'ri-stop-circle-line' : 'ri-play-circle-line'" />
          </button>
        </template>
      </div>
    </div>

    <!-- Stats bar -->
    <div class="stats-bar">
      <span>Total: <strong>{{ store.totalReceived }}</strong></span>
      <span>Rate: <strong>{{ store.ratePerSec }}</strong> msg/s</span>
      <span v-if="store.paused" class="paused-badge">
        <i class="ri-pause-circle-line" /> Paused ({{ store.pauseBuffer.length }} buffered)
      </span>
      <div class="filter-box">
        <i class="ri-search-line" />
        <input v-model="store.filterKeyword" type="text" placeholder="Filter..." />
      </div>
      <button class="btn-icon" title="导出消息" @click="openExportDialog">
        <i class="ri-download-line" />
      </button>
      <div class="notify-presets-wrap">
        <button class="btn-icon" title="Keyspace 通知预设" @click="showNotifyPresets = !showNotifyPresets">
          <i class="ri-notification-3-line" />
        </button>
        <div v-if="showNotifyPresets" class="notify-presets-dropdown">
          <div class="presets-header">Keyspace 通知预设</div>
          <button class="preset-btn" :disabled="notifyLoading" @click="applyNotifyPreset('KE$')">
            <i class="ri-key-line" /> 键空间 + 通用命令
          </button>
          <button class="preset-btn" :disabled="notifyLoading" @click="applyNotifyPreset('KElshzxe')">
            <i class="ri-key-2-line" /> 键空间 + 全部事件
          </button>
          <button class="preset-btn" :disabled="notifyLoading" @click="applyNotifyPreset('Eg')">
            <i class="ri-flashlight-line" /> 键事件 + 通用命令
          </button>
          <button class="preset-btn" :disabled="notifyLoading" @click="applyNotifyPreset('AKE')">
            <i class="ri-fullscreen-line" /> 全部通知
          </button>
          <button class="preset-btn" :disabled="notifyLoading" @click="applyNotifyPreset('')">
            <i class="ri-close-circle-line" /> 关闭通知
          </button>
        </div>
      </div>
    </div>

    <!-- Message stream -->
    <div ref="streamRef" class="message-stream">
      <div v-if="store.filteredMessages.length === 0" class="empty-state">
        <i class="ri-broadcast-line" />
        <p v-if="!store.hasSubscriptions">Subscribe to a channel to start receiving messages</p>
        <p v-else>Waiting for messages...</p>
      </div>
      <div
        v-for="(msg, idx) in store.filteredMessages"
        :key="idx"
        class="msg-row"
      >
        <span class="msg-time">{{ formatTime(msg.timestamp) }}</span>
        <span class="msg-channel">{{ msg.channel }}</span>
        <span class="msg-body">{{ msg.message }}</span>
      </div>
    </div>

    <!-- Export dialog -->
    <Transition name="modal">
      <div v-if="showExportDialog" class="modal-overlay" @click.self="showExportDialog = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3><i class="ri-download-line" /> 导出消息</h3>
          </div>
          <div class="modal-body">
            <div class="export-option">
              <span class="export-label">格式：</span>
              <label class="export-radio"><input v-model="exportFormat" type="radio" value="json" /> JSON 数组</label>
              <label class="export-radio"><input v-model="exportFormat" type="radio" value="ndjson" /> NDJSON</label>
            </div>
            <div class="export-option">
              <span class="export-label">范围：</span>
              <label class="export-radio"><input v-model="exportScope" type="radio" value="all" /> 全部消息</label>
              <label class="export-radio"><input v-model="exportScope" type="radio" value="filtered" /> 筛选结果</label>
              <label class="export-radio"><input v-model="exportScope" type="radio" value="channel" /> 指定频道</label>
            </div>
            <div v-if="exportScope === 'channel'" class="export-channel-input">
              <input v-model="exportChannel" type="text" placeholder="频道名称..." class="channel-input" />
            </div>
            <div class="export-preview">
              <span class="export-label">预览：</span>
              <code>{{ getExportData().substring(0, 200) }}{{ getExportData().length > 200 ? '...' : '' }}</code>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showExportDialog = false">取消</button>
            <button class="btn-confirm" :disabled="store.messages.length === 0" @click="handleExport">
              <i class="ri-download-line" /> 导出
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.pubsub-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--srn-color-surface-1);
}

.pubsub-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--srn-color-border);
  gap: 12px;
}

.subscribe-form {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.channel-input {
  flex: 1;
  height: 30px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 10px;
  font-size: 12px;
  background: var(--srn-color-surface-2);
  color: var(--srn-color-text-1);
  outline: none;
}
.channel-input:focus { border-color: var(--srn-color-info); }

.pattern-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--srn-color-text-2);
  cursor: pointer;
  white-space: nowrap;
}
.pattern-toggle input { margin: 0; }

.btn-subscribe {
  height: 30px;
  padding: 0 12px;
  border: none;
  border-radius: var(--srn-radius-sm);
  background: var(--srn-color-info);
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}
.btn-subscribe:disabled { opacity: 0.5; cursor: not-allowed; }

.toolbar-actions {
  display: flex;
  gap: 4px;
}

.btn-icon {
  width: 28px;
  height: 28px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  background: transparent;
  color: var(--srn-color-text-2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}
.btn-icon:hover { background: var(--srn-color-surface-2); }
.btn-icon.active { background: var(--srn-color-warning); color: #fff; border-color: var(--srn-color-warning); }

.subscriptions-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border-bottom: 1px solid var(--srn-color-border);
  flex-wrap: wrap;
}

.sub-label {
  font-size: 11px;
  color: var(--srn-color-text-3);
}

.sub-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(59, 130, 246, 0.1);
  color: var(--srn-color-info);
  font-size: 11px;
  font-family: var(--srn-font-mono);
}
.sub-tag.pattern { background: rgba(168, 85, 247, 0.1); color: #a855f7; }
.sub-tag i { cursor: pointer; font-size: 12px; }
.sub-tag i:hover { color: var(--srn-color-primary); }

.stats-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 6px 16px;
  border-bottom: 1px solid var(--srn-color-border);
  font-size: 11px;
  color: var(--srn-color-text-3);
}
.stats-bar strong { color: var(--srn-color-text-1); }

.paused-badge {
  color: var(--srn-color-warning);
  display: flex;
  align-items: center;
  gap: 4px;
}

.filter-box {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--srn-color-text-3);
}
.filter-box input {
  width: 140px;
  height: 22px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 6px;
  font-size: 11px;
  background: var(--srn-color-surface-2);
  color: var(--srn-color-text-1);
  outline: none;
}

.message-stream {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  font-family: var(--srn-font-mono);
  font-size: 12px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--srn-color-text-3);
  gap: 8px;
}
.empty-state i { font-size: 36px; }
.empty-state p { font-size: 13px; }

.msg-row {
  display: flex;
  gap: 12px;
  padding: 3px 16px;
  line-height: 1.5;
}
.msg-row:hover { background: var(--srn-color-surface-2); }

.msg-time { color: var(--srn-color-text-3); flex-shrink: 0; }
.msg-channel { color: var(--srn-color-info); flex-shrink: 0; min-width: 80px; }
.msg-body { color: var(--srn-color-text-1); word-break: break-all; }

.publish-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
}
.pub-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(34, 197, 94, 0.12);
  color: #22c55e;
  font-family: var(--srn-font-mono);
  flex-shrink: 0;
}
.pub-channel-input, .pub-msg-input {
  height: 28px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 8px;
  font-size: 12px;
  font-family: var(--srn-font-mono);
  background: var(--srn-color-surface-1);
  color: var(--srn-color-text-1);
  outline: none;
}
.pub-channel-input { width: 140px; flex-shrink: 0; }
.pub-msg-input { flex: 1; }
.pub-channel-input:focus, .pub-msg-input:focus { border-color: var(--srn-color-info); }
.btn-publish {
  height: 28px;
  padding: 0 12px;
  border: none;
  border-radius: var(--srn-radius-sm);
  background: #22c55e;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}
.btn-publish:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-publish:not(:disabled):hover { opacity: 0.9; }

/* Repeat controls */
.repeat-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 4px;
}
.repeat-toggle {
  display: flex;
  align-items: center;
  gap: 2px;
  cursor: pointer;
  color: var(--srn-color-text-3);
  font-size: 14px;
}
.repeat-toggle input { margin: 0; }
.repeat-toggle:hover { color: var(--srn-color-info); }
.repeat-interval, .repeat-max {
  width: 44px;
  height: 24px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 4px;
  font-size: 11px;
  font-family: var(--srn-font-mono);
  background: var(--srn-color-surface-1);
  color: var(--srn-color-text-1);
  outline: none;
  text-align: center;
}
.repeat-unit { font-size: 11px; color: var(--srn-color-text-3); }
.repeat-count {
  font-size: 11px;
  font-family: var(--srn-font-mono);
  color: var(--srn-color-info);
  min-width: 16px;
  text-align: center;
}
.btn-sm-repeat {
  width: 24px;
  height: 24px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  background: transparent;
  color: var(--srn-color-text-2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}
.btn-sm-repeat.active { color: var(--srn-color-primary); border-color: var(--srn-color-primary); }
.btn-sm-repeat:hover { background: var(--srn-color-surface-2); }

/* Subscription pause/resume */
.sub-tag { position: relative; }
.sub-tag.paused { opacity: 0.5; background: rgba(234, 179, 8, 0.12); color: var(--srn-color-warning); }
.sub-pause-btn {
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  padding: 0;
  font-size: 11px;
  display: inline-flex;
  align-items: center;
}
.sub-pause-btn:hover { color: var(--srn-color-info); }

/* Notify presets dropdown */
.notify-presets-wrap { position: relative; }
.notify-presets-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: var(--srn-color-surface-2);
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-md);
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  z-index: 100;
  min-width: 220px;
  overflow: hidden;
}
.presets-header {
  padding: 8px 12px;
  font-size: 11px;
  font-weight: 600;
  color: var(--srn-color-text-3);
  border-bottom: 1px solid var(--srn-color-border);
}
.preset-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: var(--srn-color-text-2);
  font-size: 12px;
  cursor: pointer;
  text-align: left;
}
.preset-btn:hover { background: var(--srn-color-surface-1); }
.preset-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Export modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-card {
  width: 440px;
  background: var(--srn-color-surface-2);
  border-radius: var(--srn-radius-lg);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  border: 1px solid var(--srn-color-border);
  overflow: hidden;
}
.modal-header { padding: 14px 20px; border-bottom: 1px solid var(--srn-color-border); }
.modal-header h3 { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; color: var(--srn-color-text-1); }
.modal-body { padding: 16px 20px; display: flex; flex-direction: column; gap: 12px; }
.export-option { display: flex; align-items: center; gap: 12px; font-size: 13px; }
.export-label { color: var(--srn-color-text-3); min-width: 50px; }
.export-radio { display: flex; align-items: center; gap: 4px; cursor: pointer; color: var(--srn-color-text-2); }
.export-radio input { margin: 0; }
.export-channel-input .channel-input { width: 100%; }
.export-preview {
  display: flex;
  gap: 8px;
  align-items: baseline;
  padding: 8px 12px;
  background: var(--srn-color-surface-1);
  border-radius: var(--srn-radius-sm);
  border: 1px solid var(--srn-color-border);
  max-height: 80px;
  overflow-y: auto;
}
.export-preview code {
  font-family: var(--srn-font-mono);
  font-size: 11px;
  color: var(--srn-color-text-2);
  word-break: break-all;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-1);
}
.btn-cancel, .btn-confirm {
  height: 30px;
  padding: 0 14px;
  border-radius: var(--srn-radius-sm);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}
.btn-cancel { border: 1px solid var(--srn-color-border); background: transparent; color: var(--srn-color-text-2); }
.btn-confirm { border: none; background: var(--srn-color-info); color: #fff; }
.btn-confirm:disabled { opacity: 0.5; }

.modal-enter-active, .modal-leave-active { transition: all 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
