<script setup lang="ts">
import { AvatarImage, type AvatarImageProps } from "radix-vue"
import { cn } from "@/lib/utils"

const props = defineProps<AvatarImageProps & { class?: string }>()
</script>

<template>
  <AvatarImage
    v-bind="props"
    referrerpolicy="no-referrer"
    :class="cn('aspect-square h-full w-full object-cover', props.class)"
  />
</template>
