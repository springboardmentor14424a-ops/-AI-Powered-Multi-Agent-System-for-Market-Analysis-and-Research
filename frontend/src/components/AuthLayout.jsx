import Logo from "./Logo";

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="auth-page">
      <header className="auth-header">
        <Logo />
      </header>
      <main className="auth-main">
        <div className="card narrow">
          <h1>{title}</h1>
          {subtitle && <p className="muted">{subtitle}</p>}
          {children}
        </div>
        {footer && <p className="auth-footer">{footer}</p>}
      </main>
    </div>
  );
}
