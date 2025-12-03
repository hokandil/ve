import React from 'react';
import { cn } from 'utils/cn';

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
    src?: string;
    alt?: string;
    fallback?: string;
    size?: 'sm' | 'md' | 'lg';
}

export const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
    ({ src, alt, fallback, size = 'md', className, ...props }, ref) => {
        const [imageError, setImageError] = React.useState(false);

        const sizes = {
            sm: 'h-8 w-8 text-xs',
            md: 'h-10 w-10 text-sm',
            lg: 'h-12 w-12 text-base',
        };

        const initials = fallback
            ? fallback.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
            : '?';

        return (
            <div
                ref={ref}
                className={cn(
                    'relative inline-flex items-center justify-center overflow-hidden rounded-full bg-slate-100',
                    sizes[size],
                    className
                )}
                {...props}
            >
                {src && !imageError ? (
                    <img
                        src={src}
                        alt={alt || fallback || 'Avatar'}
                        className="h-full w-full object-cover"
                        onError={() => setImageError(true)}
                    />
                ) : (
                    <span className="font-medium text-slate-600">{initials}</span>
                )}
            </div>
        );
    }
);

Avatar.displayName = 'Avatar';
