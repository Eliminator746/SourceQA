import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RegisterForm() {
  const { register } = useAuth();

  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

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

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setIsSubmitting(true);

      await register({
        email: email.trim(),
        password,
      });

      // Registration does not return a JWT in our
      // current backend, so send the user to login.
      navigate("/login", {
        replace: true,
      });
    } catch (err: any) {
      const message =
        err?.response?.data?.detail || "Unable to create your account.";

      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="register-email">Email</label>

        <input
          id="register-email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="Enter your email"
          autoComplete="email"
          disabled={isSubmitting}
        />
      </div>

      <div>
        <label htmlFor="register-password">Password</label>

        <input
          id="register-password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Create a password"
          autoComplete="new-password"
          disabled={isSubmitting}
        />
      </div>

      <div>
        <label htmlFor="confirm-password">Confirm password</label>

        <input
          id="confirm-password"
          type="password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          placeholder="Confirm your password"
          autoComplete="new-password"
          disabled={isSubmitting}
        />
      </div>

      {error && <p role="alert">{error}</p>}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creating account..." : "Create account"}
      </button>

      <p>
        Already have an account? <Link to="/login">Login</Link>
      </p>
    </form>
  );
}
