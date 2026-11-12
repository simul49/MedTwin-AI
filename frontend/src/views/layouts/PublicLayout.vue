<script setup lang="ts">
import PublicNav from '@/components/layout/PublicNav.vue';
import PublicFooter from '@/components/layout/PublicFooter.vue';
import SiteChatbot from '@/components/chat/SiteChatbot.vue';
</script>

<template>
  <div class="flex min-h-screen flex-col bg-transparent">
    <PublicNav />
    <main class="flex-1">
      <RouterView v-slot="{ Component, route }">
        <Transition name="page" appear>
          <component :is="Component" :key="route.path" />
        </Transition>
      </RouterView>
    </main>
    <PublicFooter />
    <SiteChatbot />
  </div>
</template>
