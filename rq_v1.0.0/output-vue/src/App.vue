<template>
  <t-config-provider :global-config="globalConfig">
    <router-view />
  </t-config-provider>
</template>

<script setup>
import { ref } from 'vue'

const globalConfig = ref({
  // TDesign 全局配置
  classPrefix: 't'
})
</script>

<style>
#app {
  min-height: 100vh;
}
</style>
