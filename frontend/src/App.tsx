import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuthStore } from './stores/authStore';
import { Layout } from './components/layout/Layout';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { ChatPage } from './pages/ChatPage';
import { QuizPage } from './pages/QuizPage';
import { TestCenterPage } from './pages/TestCenterPage';
import { CreateStudyPlanPage } from './pages/CreateStudyPlanPage';
import { StudyPlansPage } from './pages/StudyPlansPage';
import { StudyPlanDetailPage } from './pages/StudyPlanDetailPage';
import { Loading } from './components/ui/Loading';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Public Route Component (redirect to dashboard if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// Placeholder pages for routes not yet implemented
const AnalyticsPage = () => (
  <div>
    <h1 className="text-3xl font-bold mb-4">Analytics</h1>
    <p className="text-muted-foreground">Analytics page coming soon...</p>
  </div>
);

const ResourcesPage = () => (
  <div>
    <h1 className="text-3xl font-bold mb-4">Resources</h1>
    <p className="text-muted-foreground">Resources page coming soon...</p>
  </div>
);

const SettingsPage = () => (
  <div>
    <h1 className="text-3xl font-bold mb-4">Settings</h1>
    <p className="text-muted-foreground">Settings page coming soon...</p>
  </div>
);

function App() {
  const { isAuthenticated, fetchProfile } = useAuthStore();
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          await fetchProfile();
        } catch (error) {
          console.error('Failed to fetch profile:', error);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading size="lg" text="Loading..." />
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: 'hsl(var(--card))',
            color: 'hsl(var(--card-foreground))',
            border: '1px solid hsl(var(--border))',
          },
        }}
      />

      <Routes>
        {/* Public Routes */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <RegisterPage />
            </PublicRoute>
          }
        />

        {/* Protected Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <DashboardPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/study-plans"
          element={
            <ProtectedRoute>
              <Layout>
                <StudyPlansPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/study-plans/create"
          element={
            <ProtectedRoute>
              <Layout>
                <CreateStudyPlanPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/study-plans/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <StudyPlanDetailPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <Layout>
                <ChatPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/quiz"
          element={
            <ProtectedRoute>
              <Layout>
                <QuizPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/test-center"
          element={
            <ProtectedRoute>
              <Layout>
                <TestCenterPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <Layout>
                <AnalyticsPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/resources"
          element={
            <ProtectedRoute>
              <Layout>
                <ResourcesPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Layout>
                <SettingsPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Default redirect */}
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />

        {/* 404 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
