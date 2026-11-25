import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import api from "../api/client";

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    const oauthError = searchParams.get("error");

    if (oauthError) {
      setError(oauthError);
      return;
    }

    if (!token) {
      setError("Authentication token was not returned.");
      return;
    }

    localStorage.setItem("token", token);
    api
      .get("/auth/me")
      .then((res) => {
        localStorage.setItem("user", JSON.stringify(res.data));
        navigate("/dashboard", { replace: true });
      })
      .catch(() => {
        localStorage.removeItem("token");
        setError("Could not complete sign-in session.");
      });
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-[#06071A] text-white flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-[#0E1029] border border-white/10 rounded-2xl p-8 text-center space-y-4">
        {error ? (
          <>
            <p className="text-red-300 text-sm">{error}</p>
            <Link
              to="/login"
              className="inline-block px-4 py-2 rounded-lg bg-[#682EC7] text-sm font-medium"
            >
              Back to Sign In
            </Link>
          </>
        ) : (
          <p className="text-sm text-slate-300">Completing sign-in...</p>
        )}
      </div>
    </div>
  );
}