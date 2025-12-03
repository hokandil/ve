import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ShoppingBag, Users, CheckSquare, Mail, CreditCard, UserCog } from 'lucide-react';
import { cn } from '../../utils/cn';

const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Marketplace', href: '/marketplace', icon: ShoppingBag },
    { name: 'My Team', href: '/my-team', icon: Users },
    { name: 'Tasks', href: '/tasks', icon: CheckSquare },
    { name: 'Messages', href: '/messages', icon: Mail },
    { name: 'Billing', href: '/billing', icon: CreditCard },
];

export const Sidebar: React.FC = () => {
    return (
        <div className="flex h-full w-64 flex-col bg-slate-900">
            <div className="flex h-16 items-center px-6">
                <h1 className="text-xl font-bold text-white">VE Platform</h1>
            </div>
            <nav className="flex-1 space-y-1 px-3 py-4">
                {navigation.map((item) => (
                    <NavLink
                        key={item.name}
                        to={item.href}
                        className={({ isActive }) =>
                            cn(
                                'group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
                                isActive
                                    ? 'bg-slate-800 text-white'
                                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                            )
                        }
                    >
                        <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
                        {item.name}
                    </NavLink>
                ))}
            </nav>
        </div>
    );
};
