import React from 'react';
import { Menu, Transition } from '@headlessui/react';
import { Bell, User, LogOut } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { Avatar } from '../ui';

export const Header: React.FC = () => {
    const { user, signOut } = useAuth();

    return (
        <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
            <div className="flex items-center">
                <h2 className="text-lg font-semibold text-slate-900">Welcome back!</h2>
            </div>

            <div className="flex items-center gap-4">
                {/* Notifications */}
                <button className="relative rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600">
                    <Bell className="h-5 w-5" />
                    <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500"></span>
                </button>

                {/* User Menu */}
                <Menu as="div" className="relative">
                    <Menu.Button className="flex items-center gap-2 rounded-full hover:bg-slate-100 p-1">
                        <Avatar
                            src={user?.user_metadata?.avatar_url}
                            fallback={user?.email || 'U'}
                            size="sm"
                        />
                    </Menu.Button>
                    <Transition
                        as={React.Fragment}
                        enter="transition ease-out duration-100"
                        enterFrom="transform opacity-0 scale-95"
                        enterTo="transform opacity-100 scale-100"
                        leave="transition ease-in duration-75"
                        leaveFrom="transform opacity-100 scale-100"
                        leaveTo="transform opacity-0 scale-95"
                    >
                        <Menu.Items className="absolute right-0 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                            <Menu.Item>
                                {({ active }) => (
                                    <button
                                        className={`${active ? 'bg-slate-100' : ''
                                            } flex w-full items-center px-4 py-2 text-sm text-slate-700`}
                                    >
                                        <User className="mr-3 h-4 w-4" />
                                        Profile
                                    </button>
                                )}
                            </Menu.Item>
                            <Menu.Item>
                                {({ active }) => (
                                    <button
                                        onClick={signOut}
                                        className={`${active ? 'bg-slate-100' : ''
                                            } flex w-full items-center px-4 py-2 text-sm text-slate-700`}
                                    >
                                        <LogOut className="mr-3 h-4 w-4" />
                                        Sign out
                                    </button>
                                )}
                            </Menu.Item>
                        </Menu.Items>
                    </Transition>
                </Menu>
            </div>
        </header>
    );
};
