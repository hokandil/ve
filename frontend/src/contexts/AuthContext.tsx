import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from '../services/supabase';
import { authAPI } from '../services/api';
import { User, Session, AuthChangeEvent } from '@supabase/supabase-js';

interface AuthContextType {
    user: User | null;
    loading: boolean;
    signIn: (email: string, password: string) => Promise<void>;
    signUp: (email: string, password: string, companyName: string, industry?: string, companySize?: string) => Promise<void>;
    signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check active session
        supabase.auth.getSession().then(({ data: { session } }) => {
            setUser(session?.user ?? null);
            setLoading(false);
        });

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event: AuthChangeEvent, session: Session | null) => {
            setUser(session?.user ?? null);

            // Handle token refresh
            if (event === 'TOKEN_REFRESHED') {
                console.log('Token refreshed successfully');
            }

            // Handle session expiry
            if (event === 'SIGNED_OUT') {
                console.log('Session expired or user signed out');
                // Redirect to login if needed
                if (window.location.pathname !== '/login' && window.location.pathname !== '/signup') {
                    window.location.href = '/login';
                }
            }
        });

        // Set up automatic token refresh check
        const refreshInterval = setInterval(async () => {
            const { data: { session } } = await supabase.auth.getSession();
            if (session) {
                // Check if token is about to expire (within 5 minutes)
                const expiresAt = session.expires_at;
                const now = Math.floor(Date.now() / 1000);
                const timeUntilExpiry = expiresAt ? expiresAt - now : 0;

                if (timeUntilExpiry < 300) { // Less than 5 minutes
                    console.log('Token expiring soon, refreshing...');
                    await supabase.auth.refreshSession();
                }
            }
        }, 60000); // Check every minute

        return () => {
            subscription.unsubscribe();
            clearInterval(refreshInterval);
        };
    }, []);

    const signIn = async (email: string, password: string) => {
        const response = await authAPI.login(email, password);
        // Set the session in Supabase client
        await supabase.auth.setSession({
            access_token: response.access_token,
            refresh_token: response.refresh_token,
        });
    };

    const signUp = async (email: string, password: string, companyName: string, industry?: string, companySize?: string) => {
        const response = await authAPI.signup(email, password, companyName, industry, companySize);
        // Set the session in Supabase client
        await supabase.auth.setSession({
            access_token: response.access_token,
            refresh_token: response.refresh_token,
        });
    };

    const signOut = async () => {
        const { error } = await supabase.auth.signOut();
        if (error) throw error;
    };

    return (
        <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
