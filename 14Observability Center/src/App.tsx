import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import Metrics from "@/pages/Metrics";
import Logs from "@/pages/Logs";
import Traces from "@/pages/Traces";
import Alerts from "@/pages/Alerts";
import Settings from "@/pages/Settings";
import Login from "@/pages/Login";
import { AuthProvider } from "@/hooks/useAuth";
import ProtectedRoute from "@/components/ProtectedRoute";

// 创建 QueryClient 实例
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            {/* 公开路由 */}
            <Route path="/login" element={<Login />} />
            
            {/* 受保护的路由 */}
            <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="metrics" element={<Metrics />} />
              <Route path="logs" element={<Logs />} />
              <Route path="traces" element={<Traces />} />
              <Route path="alerts" element={<Alerts />} />
              <Route path="settings" element={<Settings />} />
            </Route>
            
            {/* 404 页面 */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}