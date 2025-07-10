import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { cva, type VariantProps } from 'class-variance-authority'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        default:
          'bg-sage-900 text-sage-50 shadow hover:bg-sage-900/90 focus-visible:ring-sage-950',
        knowledge:
          'bg-knowledge-500 text-white shadow-knowledge hover:bg-knowledge-600 focus-visible:ring-knowledge-500',
        task:
          'bg-task-500 text-white shadow-task hover:bg-task-600 focus-visible:ring-task-500',
        incident:
          'bg-incident-500 text-white shadow-incident hover:bg-incident-600 focus-visible:ring-incident-500',
        rag:
          'bg-rag-500 text-white shadow-rag hover:bg-rag-600 focus-visible:ring-rag-500',
        elder:
          'bg-gradient-to-r from-elder-600 to-elder-700 text-white shadow-elder hover:from-elder-700 hover:to-elder-800 focus-visible:ring-elder-600',
        ghost:
          'hover:bg-sage-100 hover:text-sage-900 dark:hover:bg-sage-800 dark:hover:text-sage-50',
        outline:
          'border border-sage-200 bg-white shadow-sm hover:bg-sage-100 hover:text-sage-900 dark:border-sage-800 dark:bg-sage-950 dark:hover:bg-sage-800 dark:hover:text-sage-50',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-10 rounded-md px-8',
        icon: 'h-9 w-9',
      },
      glow: {
        true: 'animate-sage-glow',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
      glow: false,
    },
  }
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, glow, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, glow, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }