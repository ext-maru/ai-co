import { HTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { cva, type VariantProps } from 'class-variance-authority'

const cardVariants = cva(
  'rounded-lg border bg-card text-card-foreground transition-all duration-200',
  {
    variants: {
      variant: {
        default: 'border-sage-200 bg-white shadow-sm dark:border-sage-800 dark:bg-sage-950',
        knowledge: 'border-knowledge-200 bg-knowledge-50 shadow-knowledge dark:border-knowledge-800 dark:bg-knowledge-950',
        task: 'border-task-200 bg-task-50 shadow-task dark:border-task-800 dark:bg-task-950',
        incident: 'border-incident-200 bg-incident-50 shadow-incident dark:border-incident-800 dark:bg-incident-950',
        rag: 'border-rag-200 bg-rag-50 shadow-rag dark:border-rag-800 dark:bg-rag-950',
        elder: 'border-elder-200 bg-gradient-to-br from-elder-50 to-elder-100 shadow-elder dark:border-elder-800 dark:from-elder-950 dark:to-elder-900',
      },
      hover: {
        true: 'hover:shadow-lg hover:scale-[1.02]',
        false: '',
      },
      glow: {
        true: 'animate-sage-glow',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      hover: false,
      glow: false,
    },
  }
)

export interface CardProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, hover, glow, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant, hover, glow }), className)}
      {...props}
    />
  )
)
Card.displayName = 'Card'

const CardHeader = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5 p-6', className)}
    {...props}
  />
))
CardHeader.displayName = 'CardHeader'

const CardTitle = forwardRef<
  HTMLParagraphElement,
  HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn('font-semibold leading-none tracking-tight', className)}
    {...props}
  />
))
CardTitle.displayName = 'CardTitle'

const CardDescription = forwardRef<
  HTMLParagraphElement,
  HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-sage-500 dark:text-sage-400', className)}
    {...props}
  />
))
CardDescription.displayName = 'CardDescription'

const CardContent = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
))
CardContent.displayName = 'CardContent'

const CardFooter = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center p-6 pt-0', className)}
    {...props}
  />
))
CardFooter.displayName = 'CardFooter'

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent, cardVariants }