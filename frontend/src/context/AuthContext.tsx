import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  login as loginApi,
  register as registerApi,
  getCurrentUser,
} from "../api/auth";

import type { LoginRequest, RegisterRequest, User } from "../types/auth";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);

  const [isLoading, setIsLoading] = useState(true);

  // --------------------------------------------------
  // Restore existing authentication session
  // --------------------------------------------------

  useEffect(() => {
    const restoreSession = async () => {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();

        setUser(currentUser);
      } catch {
        // Token is invalid or expired.
        localStorage.removeItem("access_token");

        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  // --------------------------------------------------
  // Login
  // --------------------------------------------------

  const login = async (data: LoginRequest): Promise<void> => {
    const response = await loginApi(data);

    localStorage.setItem("access_token", response.access_token);

    const currentUser = await getCurrentUser();

    setUser(currentUser);
  };

  // --------------------------------------------------
  // Register
  // --------------------------------------------------

  const register = async (data: RegisterRequest): Promise<User> => {
    const newUser = await registerApi(data);

    return newUser;
  };

  // --------------------------------------------------
  // Logout
  // --------------------------------------------------

  const logout = (): void => {
    localStorage.removeItem("access_token");

    setUser(null);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: user !== null,
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// --------------------------------------------------
// Custom hook
// --------------------------------------------------

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}
