<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import { AvatarRoot } from "radix-vue"
import { cn } from "@/lib/utils"

const props = defineProps<{
  class?: HTMLAttributes["class"]
}>()
</script>

<template>
  <AvatarRoot
    :class="
      cn(
        'relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full border border-border/50 shadow-sm',
        props.class
      )
    "
  >
    <slot />
  </AvatarRoot>
</template>
