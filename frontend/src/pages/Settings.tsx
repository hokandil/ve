import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Save, User, Lock, Bell, Building } from 'lucide-react';
import { PageLayout } from '../components/layout';
import { Card, CardHeader, CardTitle, CardContent, Button, Input } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/ui/Toast';
import { settingsAPI } from '../services/settingsAPI';

// Schemas
const profileSchema = z.object({
    fullName: z.string().min(1, 'Full name is required'),
    email: z.string().email('Invalid email address'),
    companyName: z.string().min(1, 'Company name is required'),
    role: z.string().optional(),
});

const passwordSchema = z.object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string().min(8, 'Password must be at least 8 characters'),
}).refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
});

type ProfileFormData = z.infer<typeof profileSchema>;
type PasswordFormData = z.infer<typeof passwordSchema>;

const Settings: React.FC = () => {
    const { user } = useAuth();
    const { addToast } = useToast();
    const [activeTab, setActiveTab] = useState<'profile' | 'password' | 'notifications'>('profile');

    // Profile Form
    const {
        register: registerProfile,
        handleSubmit: handleSubmitProfile,
        formState: { errors: profileErrors, isSubmitting: isProfileSubmitting },
    } = useForm<ProfileFormData>({
        resolver: zodResolver(profileSchema),
        defaultValues: {
            fullName: user?.user_metadata?.full_name || '',
            email: user?.email || '',
            companyName: user?.user_metadata?.company_name || '',
            role: user?.user_metadata?.role || '',
        },
    });

    // Password Form
    const {
        register: registerPassword,
        handleSubmit: handleSubmitPassword,
        formState: { errors: passwordErrors, isSubmitting: isPasswordSubmitting },
        reset: resetPassword,
    } = useForm<PasswordFormData>({
        resolver: zodResolver(passwordSchema),
    });

    const onProfileSubmit = async (data: ProfileFormData) => {
        try {
            await settingsAPI.updateProfile(data);
            addToast('success', 'Profile updated successfully!');
        } catch (error) {
            console.error('Failed to update profile:', error);
            addToast('error', 'Failed to update profile');
        }
    };

    const onPasswordSubmit = async (data: PasswordFormData) => {
        try {
            await settingsAPI.updatePassword(data);
            resetPassword();
            addToast('success', 'Password updated successfully!');
        } catch (error) {
            console.error('Failed to update password:', error);
            addToast('error', 'Failed to update password');
        }
    };

    return (
        <PageLayout title="Settings">
            <div className="flex flex-col md:flex-row gap-6">
                {/* Sidebar Navigation */}
                <Card className="w-full md:w-64 flex-shrink-0 h-fit">
                    <CardContent className="p-2">
                        <nav className="space-y-1">
                            <button
                                onClick={() => setActiveTab('profile')}
                                className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === 'profile'
                                    ? 'bg-indigo-50 text-indigo-700'
                                    : 'text-slate-700 hover:bg-slate-50'
                                    }`}
                            >
                                <User className="h-4 w-4" />
                                Profile
                            </button>
                            <button
                                onClick={() => setActiveTab('password')}
                                className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === 'password'
                                    ? 'bg-indigo-50 text-indigo-700'
                                    : 'text-slate-700 hover:bg-slate-50'
                                    }`}
                            >
                                <Lock className="h-4 w-4" />
                                Password
                            </button>
                            <button
                                onClick={() => setActiveTab('notifications')}
                                className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === 'notifications'
                                    ? 'bg-indigo-50 text-indigo-700'
                                    : 'text-slate-700 hover:bg-slate-50'
                                    }`}
                            >
                                <Bell className="h-4 w-4" />
                                Notifications
                            </button>
                        </nav>
                    </CardContent>
                </Card>

                {/* Content Area */}
                <div className="flex-1">
                    {activeTab === 'profile' && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Profile Information</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleSubmitProfile(onProfileSubmit)} className="space-y-4">
                                    <div className="flex items-center gap-4 mb-6">
                                        <div className="h-20 w-20 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 text-2xl font-bold">
                                            {user?.email?.[0].toUpperCase() || 'U'}
                                        </div>
                                        <Button type="button" variant="outline" size="sm">
                                            Change Avatar
                                        </Button>
                                    </div>

                                    <div className="grid gap-4 md:grid-cols-2">
                                        <Input
                                            label="Full Name"
                                            error={profileErrors.fullName?.message}
                                            {...registerProfile('fullName')}
                                        />
                                        <Input
                                            label="Email Address"
                                            type="email"
                                            disabled
                                            error={profileErrors.email?.message}
                                            {...registerProfile('email')}
                                        />
                                    </div>

                                    <div className="grid gap-4 md:grid-cols-2">
                                        <Input
                                            label="Company Name"
                                            icon={<Building className="h-4 w-4" />}
                                            error={profileErrors.companyName?.message}
                                            {...registerProfile('companyName')}
                                        />
                                        <Input
                                            label="Role / Job Title"
                                            error={profileErrors.role?.message}
                                            {...registerProfile('role')}
                                        />
                                    </div>

                                    <div className="flex justify-end pt-4">
                                        <Button type="submit" isLoading={isProfileSubmitting}>
                                            <Save className="mr-2 h-4 w-4" />
                                            Save Changes
                                        </Button>
                                    </div>
                                </form>
                            </CardContent>
                        </Card>
                    )}

                    {activeTab === 'password' && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Change Password</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleSubmitPassword(onPasswordSubmit)} className="space-y-4 max-w-md">
                                    <Input
                                        label="Current Password"
                                        type="password"
                                        error={passwordErrors.currentPassword?.message}
                                        {...registerPassword('currentPassword')}
                                    />
                                    <Input
                                        label="New Password"
                                        type="password"
                                        error={passwordErrors.newPassword?.message}
                                        {...registerPassword('newPassword')}
                                    />
                                    <Input
                                        label="Confirm New Password"
                                        type="password"
                                        error={passwordErrors.confirmPassword?.message}
                                        {...registerPassword('confirmPassword')}
                                    />

                                    <div className="flex justify-end pt-4">
                                        <Button type="submit" isLoading={isPasswordSubmitting}>
                                            <Save className="mr-2 h-4 w-4" />
                                            Update Password
                                        </Button>
                                    </div>
                                </form>
                            </CardContent>
                        </Card>
                    )}

                    {activeTab === 'notifications' && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Notification Preferences</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                                        <div>
                                            <h4 className="font-medium text-slate-900">Task Updates</h4>
                                            <p className="text-sm text-slate-500">Receive notifications when tasks are updated</p>
                                        </div>
                                        <input type="checkbox" defaultChecked className="h-4 w-4 text-indigo-600 rounded border-slate-300" />
                                    </div>

                                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                                        <div>
                                            <h4 className="font-medium text-slate-900">New Messages</h4>
                                            <p className="text-sm text-slate-500">Receive notifications for new messages from VEs</p>
                                        </div>
                                        <input type="checkbox" defaultChecked className="h-4 w-4 text-indigo-600 rounded border-slate-300" />
                                    </div>

                                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                                        <div>
                                            <h4 className="font-medium text-slate-900">Billing Alerts</h4>
                                            <p className="text-sm text-slate-500">Receive notifications about billing and usage</p>
                                        </div>
                                        <input type="checkbox" defaultChecked className="h-4 w-4 text-indigo-600 rounded border-slate-300" />
                                    </div>

                                    <div className="flex justify-end pt-4">
                                        <Button>
                                            <Save className="mr-2 h-4 w-4" />
                                            Save Preferences
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </PageLayout>
    );
};

export default Settings;
