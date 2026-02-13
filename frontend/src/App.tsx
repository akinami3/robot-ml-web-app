import { Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { LoginPage } from "@/pages/LoginPage";
import { SignupPage } from "@/pages/SignupPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { ManualControlPage } from "@/pages/ManualControlPage";
import { NavigationPage } from "@/pages/NavigationPage";
import { SensorViewPage } from "@/pages/SensorViewPage";
import { DataManagementPage } from "@/pages/DataManagementPage";
import { RAGChatPage } from "@/pages/RAGChatPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { useAuthStore } from "@/stores/authStore";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const accessToken = useAuthStore((s) => s.accessToken);
  if (!accessToken) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="control" element={<ManualControlPage />} />
        <Route path="navigation" element={<NavigationPage />} />
        <Route path="sensors" element={<SensorViewPage />} />
        <Route path="data" element={<DataManagementPage />} />
        <Route path="rag" element={<RAGChatPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
