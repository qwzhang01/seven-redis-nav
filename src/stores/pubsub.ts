import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { PubSubMessage } from '@/types/phase2';

const MAX_MESSAGES = 5000;

export const usePubSubStore = defineStore('pubsub', () => {
  // Ring buffer for messages
  const messages = ref<PubSubMessage[]>([]);
  const subscriptions = ref<string[]>([]);
  const patternSubscriptions = ref<string[]>([]);
  const paused = ref(false);
  const pauseBuffer = ref<PubSubMessage[]>([]);
  const filterKeyword = ref('');
  const totalReceived = ref(0);
  const ratePerSec = ref(0);

  // Rate tracking
  let rateCounter = 0;
  let rateInterval: ReturnType<typeof setInterval> | null = null;

  function startRateTracking() {
    if (rateInterval) return;
    rateInterval = setInterval(() => {
      ratePerSec.value = rateCounter;
      rateCounter = 0;
    }, 1000);
  }

  function stopRateTracking() {
    if (rateInterval) {
      clearInterval(rateInterval);
      rateInterval = null;
    }
    ratePerSec.value = 0;
  }

  // Per-channel message counts
  const channelCounts = ref<Record<string, number>>({});

  function addMessage(msg: PubSubMessage) {
    totalReceived.value++;
    rateCounter++;

    // Track per-channel count
    channelCounts.value[msg.channel] = (channelCounts.value[msg.channel] || 0) + 1;

    if (paused.value) {
      pauseBuffer.value.push(msg);
      return;
    }

    pushToRingBuffer(msg);
  }

  function pushToRingBuffer(msg: PubSubMessage) {
    messages.value.push(msg);
    if (messages.value.length > MAX_MESSAGES) {
      messages.value.shift();
    }
  }

  function resume() {
    paused.value = false;
    // Flush pause buffer
    for (const msg of pauseBuffer.value) {
      pushToRingBuffer(msg);
    }
    pauseBuffer.value = [];
  }

  function pause() {
    paused.value = true;
  }

  function clearMessages() {
    messages.value = [];
    pauseBuffer.value = [];
    totalReceived.value = 0;
    channelCounts.value = {};
    rateCounter = 0;
    ratePerSec.value = 0;
  }

  function addSubscription(channels: string[], pattern: boolean) {
    if (pattern) {
      for (const ch of channels) {
        if (!patternSubscriptions.value.includes(ch)) {
          patternSubscriptions.value.push(ch);
        }
      }
    } else {
      for (const ch of channels) {
        if (!subscriptions.value.includes(ch)) {
          subscriptions.value.push(ch);
        }
      }
    }
    startRateTracking();
  }

  function removeSubscription(channels: string[], pattern: boolean) {
    if (pattern) {
      patternSubscriptions.value = patternSubscriptions.value.filter(
        (ch) => !channels.includes(ch),
      );
    } else {
      subscriptions.value = subscriptions.value.filter(
        (ch) => !channels.includes(ch),
      );
    }
    if (subscriptions.value.length === 0 && patternSubscriptions.value.length === 0) {
      stopRateTracking();
    }
  }

  function reset() {
    clearMessages();
    subscriptions.value = [];
    patternSubscriptions.value = [];
    stopRateTracking();
  }

  const filteredMessages = computed(() => {
    if (!filterKeyword.value) return messages.value;
    const kw = filterKeyword.value.toLowerCase();
    return messages.value.filter(
      (m) =>
        m.channel.toLowerCase().includes(kw) ||
        m.message.toLowerCase().includes(kw),
    );
  });

  const hasSubscriptions = computed(
    () => subscriptions.value.length > 0 || patternSubscriptions.value.length > 0,
  );

  return {
    messages,
    subscriptions,
    patternSubscriptions,
    paused,
    pauseBuffer,
    filterKeyword,
    totalReceived,
    ratePerSec,
    channelCounts,
    filteredMessages,
    hasSubscriptions,
    addMessage,
    pause,
    resume,
    clearMessages,
    addSubscription,
    removeSubscription,
    reset,
  };
});
