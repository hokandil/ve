import React from 'react';
import { cn } from 'utils/cn';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'secondary' | 'outline';
    children: React.ReactNode;
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
    ({ variant = 'default', className, children, ...props }, ref) => {
        const variants = {
            default: 'bg-slate-100 text-slate-800',
            success: 'bg-green-100 text-green-800',
            warning: 'bg-amber-100 text-amber-800',
            error: 'bg-red-100 text-red-800',
            info: 'bg-blue-100 text-blue-800',
            secondary: 'bg-slate-200 text-slate-900',
            outline: 'text-slate-900 border border-slate-200',
        };

        return (
            <span
                ref={ref}
                className={cn(
                    'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors',
                    variants[variant],
                    className
                )}
                {...props}
            >
                {children}
            </span>
        );
    }
);

Badge.displayName = 'Badge';
