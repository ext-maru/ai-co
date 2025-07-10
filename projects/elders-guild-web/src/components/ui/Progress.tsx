'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { cva, type VariantProps } from 'class-variance-authority'

const progressVariants = cva(
  'relative h-2 w-full overflow-hidden rounded-full',
  {
    variants: {
      variant: {
        default: 'bg-sage-200 dark:bg-sage-800',
        knowledge: 'bg-knowledge-200 dark:bg-knowledge-800',
        task: 'bg-task-200 dark:bg-task-800',
        incident: 'bg-incident-200 dark:bg-incident-800',
        rag: 'bg-rag-200 dark:bg-rag-800',
        elder: 'bg-elder-200 dark:bg-elder-800',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

const progressIndicatorVariants = cva(
  'h-full transition-all duration-300 ease-in-out',
  {
    variants: {
      variant: {
        default: 'bg-sage-900 dark:bg-sage-50',
        knowledge: 'bg-knowledge-500 animate-knowledge-pulse',
        task: 'bg-task-500 animate-task-shimmer',
        incident: 'bg-incident-500 animate-incident-alert',
        rag: 'bg-rag-500 animate-rag-search',
        elder: 'bg-gradient-to-r from-elder-600 to-elder-700',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface ProgressProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof progressVariants> {
  value?: number
  max?: number
  showValue?: boolean
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, max = 100, variant, showValue = false, ...props }, ref) => {
    const percentage = Math.min(100, Math.max(0, (value / max) * 100))

    return (
      <div className="space-y-1">
        <div
          ref={ref}
          className={cn(progressVariants({ variant }), className)}
          {...props}
        >
          <div
            className={cn(progressIndicatorVariants({ variant }))}
            style={{ width: `${percentage}%` }}
          />
        </div>
        {showValue && (
          <div className="flex justify-between text-xs text-sage-600 dark:text-sage-400">
            <span>{value}</span>
            <span>{Math.round(percentage)}%</span>
          </div>
        )}
      </div>
    )
  }
)
Progress.displayName = 'Progress'

export { Progress }
