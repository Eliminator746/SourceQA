import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ChatPage from "./pages/ChatPage";

import ProtectedRoute from "./routes/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}

          <Route path="/login" element={<LoginPage />} />

          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes */}

          <Route element={<ProtectedRoute />}>
            <Route path="/chat" element={<ChatPage />} />
          </Route>

          {/* Unknown route */}

          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
