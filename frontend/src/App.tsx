import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ToastProvider } from './components/ui';
import { Sidebar, Header } from './components/layout';
import { ErrorBoundary } from './components/common/ErrorBoundary';

// Lazy load pages for code splitting
const Login = lazy(() => import('./pages/Login'));
const SignUp = lazy(() => import('./pages/SignUp'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Marketplace = lazy(() => import('./pages/Marketplace'));
const MyTeam = lazy(() => import('./pages/MyTeam'));
const Tasks = lazy(() => import('./pages/Tasks'));
const Messages = lazy(() => import('./pages/Messages'));
const Billing = lazy(() => import('./pages/Billing'));
const OrgChart = lazy(() => import('./pages/OrgChart'));
const Settings = lazy(() => import('./pages/Settings'));
const Chat = lazy(() => import('./pages/Chat'));

// Loading fallback component
const PageLoader = () => (
    <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
    </div>
);

const PrivateRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
            </div>
        );
    }

    return user ? children : <Navigate to="/login" />;
};

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return (
        <div className="flex h-screen overflow-hidden bg-slate-50">
            <Sidebar />
            <div className="flex flex-1 flex-col overflow-hidden">
                <Header />
                <main className="flex-1 overflow-auto">{children}</main>
            </div>
        </div>
    );
};

function App() {
    return (
        <Router>
            <AuthProvider>
                <ToastProvider>
                    <ErrorBoundary>
                        <Suspense fallback={<PageLoader />}>
                            <Routes>
                                <Route path="/login" element={<Login />} />
                                <Route path="/signup" element={<SignUp />} />
                                <Route
                                    path="/dashboard"
                                    element={
                                        <PrivateRoute>
                                            <AppLayout>
                                                <Dashboard />
                                            </AppLayout>
                                        </PrivateRoute>
                                    }
                                />
                                <Route
                                    path="/marketplace"
                                    element={
                                        <PrivateRoute>
                                            <AppLayout>
                                                <Marketplace />
                                            </AppLayout>
                                        </PrivateRoute>
                                    }
                                />
                                <Route
                                    path="/my-team"
                                    element={
                                        <PrivateRoute>
                                            <AppLayout>
                                                <MyTeam />
                                            </AppLayout>
                                        </PrivateRoute>
                                    }
                                />
                                <Route
                                    path="/chat"
                                    element={
                                        <PrivateRoute>
                                            <AppLayout>
                                                <Chat />
                                            </AppLayout>
                                        </PrivateRoute>
                                    }
                                />
                                <Route
                                    path="/tasks"
                                    element={
                                        <PrivateRoute>
                                            <AppLayout>
                                                <Tasks />
                                            </AppLayout>
                                        </PrivateRoute>
                                    }
                                />
                                <Route
                                    path="/messages"
                                    element={
                                        <PrivateRoute>
                                            <AppLayout>
                                                <Messages />
                                            </AppLayout>
                                        </PrivateRoute>
                                    }
                                />
                                <Route
                                    path="/billing"
                                    element={
                                        <PrivateRoute>
                                            <AppLayout>
                                                <Billing />
                                            </AppLayout>
                                        </PrivateRoute>
                                    }
                                />
                                <Route
                                    path="/org-chart"
                                    element={
                                        <PrivateRoute>
                                            <AppLayout>
                                                <OrgChart />
                                            </AppLayout>
                                        </PrivateRoute>
                                    }
                                />
                                <Route
                                    path="/settings"
                                    element={
                                        <PrivateRoute>
                                            <AppLayout>
                                                <Settings />
                                            </AppLayout>
                                        </PrivateRoute>
                                    }
                                />
                                <Route path="/" element={<Navigate to="/dashboard" />} />
                            </Routes>
                        </Suspense>
                    </ErrorBoundary>
                </ToastProvider>
            </AuthProvider>
        </Router>
    );
}

export default App;
