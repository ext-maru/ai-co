import { HTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-sage-900 text-sage-50 shadow hover:bg-sage-900/80 dark:bg-sage-50 dark:text-sage-900 dark:hover:bg-sage-50/80',
        secondary:
          'border-transparent bg-sage-100 text-sage-900 hover:bg-sage-100/80 dark:bg-sage-800 dark:text-sage-50 dark:hover:bg-sage-800/80',
        destructive:
          'border-transparent bg-red-500 text-red-50 shadow hover:bg-red-500/80 dark:bg-red-900 dark:text-red-50 dark:hover:bg-red-900/80',
        outline: 'text-foreground',
        knowledge:
          'border-transparent bg-knowledge-500 text-white shadow hover:bg-knowledge-500/80',
        task:
          'border-transparent bg-task-500 text-white shadow hover:bg-task-500/80',
        incident:
          'border-transparent bg-incident-500 text-white shadow hover:bg-incident-500/80',
        rag:
          'border-transparent bg-rag-500 text-white shadow hover:bg-rag-500/80',
        elder:
          'border-transparent bg-gradient-to-r from-elder-600 to-elder-700 text-white shadow hover:from-elder-700 hover:to-elder-800',
      },
      size: {
        default: 'px-2.5 py-0.5 text-xs',
        sm: 'px-2 py-0.5 text-[10px]',
        lg: 'px-3 py-1 text-sm',
      },
      pulse: {
        true: 'animate-pulse',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
      pulse: false,
    },
  }
)

export interface BadgeProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

const Badge = forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant, size, pulse, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(badgeVariants({ variant, size, pulse }), className)}
        {...props}
      />
    )
  }
)
Badge.displayName = 'Badge'

export { Badge, badgeVariants }
