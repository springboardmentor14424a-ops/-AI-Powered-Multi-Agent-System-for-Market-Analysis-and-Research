import { GoogleLogin } from "@react-oauth/google";
import axios from "axios";

function GoogleLoginButton({ onLogin }) {

  const handleSuccess = async (response) => {
    try {
      const result = await axios.post(
        "http://127.0.0.1:8000/auth/google",
        {
          credential: response.credential
        }
      );

      onLogin(
        result.data.access_token,
        result.data.user
      );

    } catch (error) {
      alert(
        error.response?.data?.detail ||
        "Google login failed"
      );
    }
  };

  return (
    <GoogleLogin
      onSuccess={handleSuccess}
      onError={() => {
        alert("Google sign-in was unsuccessful");
      }}
    />
  );
}

export default GoogleLoginButton;