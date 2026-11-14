
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";

function Settings() {
  const navigate = useNavigate();

  const user = JSON.parse(
    sessionStorage.getItem("user") || "null"
  );
  const token = sessionStorage.getItem("access_token");

  useEffect(() => {
    if (!token || !user) {
      navigate("/login", { replace: true });
    }
  }, [navigate, token, user]);

  const logout = () => {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");
    navigate("/login");
  };

  const settingsOptions = [
    {
      title: "Theme",
      description: "Customise the appearance of your StockIntel workspace.",
      icon: "◐",
      action: () => {},
    },
    {
      title: "Basic Settings",
      description: "Manage your general workspace settings.",
      icon: "⚙",
      action: () => {},
    },
    {
      title: "Research Preferences",
      description:
        "Choose your preferred market, analysis period, indicators, news and risk settings.",
      icon: "▤",
      action: () => navigate("/dashboard/preferences"),
    },
  ];

  return (
    <DashboardLayout user={user} onLogout={logout}>
      <div className="settings-home-wrapper">

        <div className="settings-home-header">
          <p className="eyebrow">PERSONAL SETTINGS</p>
          <h1>Settings</h1>
          <p>Manage your StockIntel workspace and preferences.</p>
        </div>

        <div className="settings-home-grid">
          {settingsOptions.map((item) => (
            <button
              type="button"
              className="settings-home-card"
              key={item.title}
              onClick={item.action}
            >
              <span className="settings-home-icon">
                {item.icon}
              </span>

              <h2>{item.title}</h2>

              <p>{item.description}</p>

              <span className="settings-home-arrow">
                Open →
              </span>
            </button>
          ))}
        </div>

      </div>
    </DashboardLayout>
  );
}

export default Settings;
