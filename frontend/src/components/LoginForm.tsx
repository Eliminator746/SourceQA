import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginForm() {
  const { login } = useAuth();

  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    setError("");

    if (!email.trim()) {
      setError("Email is required.");
      return;
    }

    if (!password) {
      setError("Password is required.");
      return;
    }

    try {
      setIsSubmitting(true);

      await login({
        email: email.trim(),
        password,
      });

      // If the user was redirected to login from
      // a protected route, send them back there.
      const from = location.state?.from?.pathname;

      navigate(from || "/chat", {
        replace: true,
      });
    } catch (err: any) {
      const message =
        err?.response?.data?.detail ||
        "Unable to login. Please check your credentials.";

      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="email">Email</label>

        <input
          id="email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="Enter your email"
          autoComplete="email"
          disabled={isSubmitting}
        />
      </div>

      <div>
        <label htmlFor="password">Password</label>

        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Enter your password"
          autoComplete="current-password"
          disabled={isSubmitting}
        />
      </div>

      {error && <p role="alert">{error}</p>}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Logging in..." : "Login"}
      </button>

      <p>
        Don't have an account? <Link to="/register">Create an account</Link>
      </p>
    </form>
  );
}
