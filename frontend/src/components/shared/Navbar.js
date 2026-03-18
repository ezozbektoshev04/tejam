import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  const links = {
    customer: [
      { to: '/', label: '🏠 Home' },
      { to: '/orders', label: '📦 My Orders' },
    ],
    business: [
      { to: '/business', label: '📊 Dashboard' },
      { to: '/business/store', label: '🏪 My Store' },
      { to: '/business/bags', label: '🛍️ Bags' },
    ],
    admin: [
      { to: '/admin', label: '📊 Dashboard' },
      { to: '/admin/users', label: '👥 Users' },
      { to: '/admin/stores', label: '🏪 Stores' },
    ],
  };

  return (
    <nav style={styles.nav}>
      <div style={styles.inner}>
        <Link to="/" style={styles.logo}>🌿 Tejam</Link>
        <div style={styles.links}>
          {(links[user.role] || []).map(link => (
            <Link key={link.to} to={link.to} style={styles.link}>
              {link.label}
            </Link>
          ))}
        </div>
        <div style={styles.right}>
          <span style={styles.userName}>👤 {user.name}</span>
          <button onClick={logout} className="btn btn-secondary" style={{padding: '6px 14px'}}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

const styles = {
  nav: {
    background: 'white',
    borderBottom: '1px solid #eee',
    position: 'sticky',
    top: 0,
    zIndex: 100,
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
  },
  inner: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 20px',
    height: '60px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logo: {
    fontSize: '1.4rem',
    fontWeight: 700,
    color: '#4caf50',
    textDecoration: 'none',
  },
  links: { display: 'flex', gap: '20px' },
  link: {
    color: '#555',
    textDecoration: 'none',
    fontWeight: 500,
    fontSize: '0.95rem',
  },
  right: { display: 'flex', alignItems: 'center', gap: '12px' },
  userName: { color: '#888', fontSize: '0.9rem' },
};