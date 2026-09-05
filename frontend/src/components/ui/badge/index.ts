import { type VariantProps, cva } from "class-variance-authority"

export { default as Badge } from "./Badge.vue"

export const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 select-none",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive/15 text-destructive border-destructive/20",
        outline: "text-foreground",
        success:
          "border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
        warning:
          "border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-400",
        info:
          "border-sky-500/20 bg-sky-500/10 text-sky-600 dark:text-sky-400",
        danger:
          "border-rose-500/20 bg-rose-500/10 text-rose-600 dark:text-rose-400",
        matrix:
          "border-indigo-500/30 bg-indigo-500/15 text-indigo-500 font-semibold shadow-sm",
        xiaohongshu:
          "border-rose-500/30 bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400 font-semibold shadow-sm",
        douyin:
          "border-slate-800/20 bg-slate-900 text-white dark:bg-slate-800 dark:text-slate-100 font-semibold shadow-sm",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export type BadgeVariants = VariantProps<typeof badgeVariants>
