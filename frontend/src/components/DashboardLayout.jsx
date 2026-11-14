
import { NavLink } from "react-router-dom";

function DashboardLayout({ user, onLogout, children }) {
  const navigation = [
    { name: "Overview", path: "/dashboard", icon: "▦" },
    { name: "Watchlist", path: "/dashboard/watchlist", icon: "☆" },
    { name: "Markets", path: "/dashboard/markets", icon: "▥" },
    { name: "Research", path: "/dashboard/research", icon: "▤" },
    { name: "History", path: "/dashboard/history", icon: "◷" },
  ];

  return (
    <div className="terminal-layout">
      <aside className="terminal-sidebar">
        <div className="sidebar-brand">
          Stock<span>Intel</span>
        </div>

        <div className="sidebar-divider" />

        <nav className="sidebar-navigation">
          <p className="sidebar-section-label">WORKSPACE</p>

          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              end={item.path === "/dashboard"}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? "active" : ""}`
              }
            >
              <span className="sidebar-icon">{item.icon}</span>
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <NavLink
            to="/dashboard/settings"
            className={({ isActive }) =>
              `sidebar-link ${isActive ? "active" : ""}`
            }
          >
            <span className="sidebar-icon">⚙</span>
            <span>Settings</span>
          </NavLink>

          <div className="sidebar-divider" />

          <div className="sidebar-user">
            <div className="sidebar-avatar">
              {user?.full_name?.charAt(0).toUpperCase() || "U"}
            </div>

            <div className="sidebar-user-info">
              <strong>{user?.full_name || "User"}</strong>
              <span>Research Workspace</span>
            </div>
          </div>

          <button className="sidebar-logout" onClick={onLogout}>
            Logout
          </button>
        </div>
      </aside>

      <div className="terminal-main">
        <header className="terminal-topbar">
          <span>STOCKINTEL / WORKSPACE</span>
          <span className="terminal-user-name">
            {user?.full_name}
          </span>
        </header>

        <main className="terminal-content">
          {children}
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;
