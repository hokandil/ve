import api from './api';

export interface ProfileUpdateData {
    fullName: string;
    companyName: string;
    role?: string;
}

export interface PasswordUpdateData {
    currentPassword: string;
    newPassword: string;
}

export const settingsAPI = {
    updateProfile: async (data: ProfileUpdateData) => {
        const response = await api.put('/customers/profile', {
            full_name: data.fullName,
            company_name: data.companyName,
            role: data.role,
        });
        return response.data;
    },

    updatePassword: async (data: PasswordUpdateData) => {
        const response = await api.post('/auth/change-password', {
            current_password: data.currentPassword,
            new_password: data.newPassword,
        });
        return response.data;
    },
};
