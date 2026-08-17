import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  const location = useLocation();

  // Wait until AuthContext has checked
  // whether an existing JWT is valid.
  if (isLoading) {
    return <div>Loading...</div>;
  }

  // User is not authenticated.
  // Remember the page they were trying to access.
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // User is authenticated.
  // Render the nested protected route.
  return <Outlet />;
}
