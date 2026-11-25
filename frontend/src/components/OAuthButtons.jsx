import { API_BASE_URL } from "../api/client";

export default function OAuthButtons({ labelPrefix = "Continue with" }) {
  const startOAuth = (provider) => {
    window.location.href = `${API_BASE_URL}/auth/oauth/${provider}`;
  };

  return (
    <div className="space-y-3">
      <div className="relative my-5">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/10" />
        </div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-[#0E1029] px-3 text-slate-400">or</span>
        </div>
      </div>

      <button
        type="button"
        onClick={() => startOAuth("google")}
        className="w-full py-2.5 px-4 rounded-lg bg-[#06071A] hover:bg-white/5 border border-white/15 text-sm font-medium flex items-center justify-center gap-2.5 transition"
      >
        <span>{labelPrefix} Google</span>
      </button>

      <button
        type="button"
        onClick={() => startOAuth("microsoft")}
        className="w-full py-2.5 px-4 rounded-lg bg-[#06071A] hover:bg-white/5 border border-white/15 text-sm font-medium flex items-center justify-center gap-2.5 transition"
      >
        <span>{labelPrefix} Microsoft</span>
      </button>
    </div>
  );
}