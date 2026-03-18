import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/axios';
import toast from 'react-hot-toast';

export default function Register() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'customer' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post('/auth/register', form);
      login(res.data.user, res.data.token);
      toast.success('Account created!');
      const role = res.data.user.role;
      if (role === 'business') navigate('/business');
      else navigate('/');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.wrapper}>
      <div style={styles.card}>
        <div style={styles.logo}>🌿 Tejam</div>
        <h2 style={styles.title}>Create account</h2>
        <p style={styles.subtitle}>Join Tejam and reduce food waste</p>

        <form onSubmit={handleSubmit}>
          <div style={styles.field}>
            <label style={styles.label}>Full Name</label>
            <input
              type="text"
              placeholder="Your name"
              value={form.name}
              onChange={e => setForm({...form, name: e.target.value})}
              required
            />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Email</label>
            <input
              type="email"
              placeholder="you@email.com"
              value={form.email}
              onChange={e => setForm({...form, email: e.target.value})}
              required
            />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Password</label>
            <input
              type="password"
              placeholder="Min 6 characters"
              value={form.password}
              onChange={e => setForm({...form, password: e.target.value})}
              required
            />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>I am a...</label>
            <select
              value={form.role}
              onChange={e => setForm({...form, role: e.target.value})}
            >
              <option value="customer">Customer — I want to buy food bags</option>
              <option value="business">Business — I want to sell food bags</option>
            </select>
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            style={{width: '100%', marginTop: '8px', padding: '12px'}}
            disabled={loading}
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p style={styles.footer}>
          Already have an account?{' '}
          <Link to="/login" style={styles.link}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}

const styles = {
  wrapper: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #e8f5e9, #f1f8e9)',
  },
  card: {
    background: 'white',
    borderRadius: '16px',
    padding: '40px',
    width: '100%',
    maxWidth: '420px',
    boxShadow: '0 4px 24px rgba(0,0,0,0.1)',
  },
  logo: { fontSize: '2rem', textAlign: 'center', marginBottom: '8px' },
  title: { textAlign: 'center', fontSize: '1.5rem', fontWeight: 700 },
  subtitle: { textAlign: 'center', color: '#888', marginBottom: '24px' },
  field: { marginBottom: '16px' },
  label: { display: 'block', marginBottom: '6px', fontWeight: 600, fontSize: '0.9rem' },
  footer: { textAlign: 'center', marginTop: '20px', color: '#888' },
  link: { color: '#4caf50', fontWeight: 600, textDecoration: 'none' },
};