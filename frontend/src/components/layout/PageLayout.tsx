import React from 'react';

export interface PageLayoutProps {
    title?: string;
    children: React.ReactNode;
}

export const PageLayout: React.FC<PageLayoutProps> = ({ title, children }) => {
    return (
        <div className="h-full overflow-auto">
            <div className="mx-auto max-w-7xl px-6 py-8">
                {title && (
                    <h1 className="mb-6 text-2xl font-bold text-slate-900">{title}</h1>
                )}
                {children}
            </div>
        </div>
    );
};
