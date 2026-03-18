import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';

// Auth pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';

// Customer pages
import CustomerHome from './pages/customer/Home';
import CustomerOrders from './pages/customer/Orders';
import StoreDetail from './pages/customer/StoreDetail';

// Business pages
import BusinessDashboard from './pages/business/Dashboard';
import ManageStore from './pages/business/ManageStore';
import ManageBags from './pages/business/ManageBags';

// Admin pages
import AdminDashboard from './pages/admin/Dashboard';
import AdminUsers from './pages/admin/Users';
import AdminStores from './pages/admin/Stores';

// Shared
import Navbar from './components/shared/Navbar';

const ProtectedRoute = ({ children, roles }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading">Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" />;
  return children;
};

function AppRoutes() {
  const { user } = useAuth();

  return (
    <>
      <Navbar />
      <Routes>
        {/* Public */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Customer */}
        <Route path="/" element={
          <ProtectedRoute roles={['customer']}>
            <CustomerHome />
          </ProtectedRoute>
        } />
        <Route path="/orders" element={
          <ProtectedRoute roles={['customer']}>
            <CustomerOrders />
          </ProtectedRoute>
        } />
        <Route path="/store/:id" element={
          <ProtectedRoute roles={['customer']}>
            <StoreDetail />
          </ProtectedRoute>
        } />

        {/* Business */}
        <Route path="/business" element={
          <ProtectedRoute roles={['business']}>
            <BusinessDashboard />
          </ProtectedRoute>
        } />
        <Route path="/business/store" element={
          <ProtectedRoute roles={['business']}>
            <ManageStore />
          </ProtectedRoute>
        } />
        <Route path="/business/bags" element={
          <ProtectedRoute roles={['business']}>
            <ManageBags />
          </ProtectedRoute>
        } />

        {/* Admin */}
        <Route path="/admin" element={
          <ProtectedRoute roles={['admin']}>
            <AdminDashboard />
          </ProtectedRoute>
        } />
        <Route path="/admin/users" element={
          <ProtectedRoute roles={['admin']}>
            <AdminUsers />
          </ProtectedRoute>
        } />
        <Route path="/admin/stores" element={
          <ProtectedRoute roles={['admin']}>
            <AdminStores />
          </ProtectedRoute>
        } />

        {/* Redirect based on role */}
        <Route path="*" element={
          user?.role === 'business' ? <Navigate to="/business" /> :
          user?.role === 'admin' ? <Navigate to="/admin" /> :
          <Navigate to="/login" />
        } />
      </Routes>
    </>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster position="top-right" />
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;