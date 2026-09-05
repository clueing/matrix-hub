<script setup lang="ts">
import { AvatarFallback, type AvatarFallbackProps } from "radix-vue"
import { cn } from "@/lib/utils"

const props = defineProps<AvatarFallbackProps & { class?: string }>()
</script>

<template>
  <AvatarFallback
    v-bind="props"
    :class="
      cn(
        'flex h-full w-full items-center justify-center rounded-full bg-muted text-xs font-semibold text-muted-foreground select-none',
        props.class
      )
    "
  >
    <slot />
  </AvatarFallback>
</template>
