import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppLayout } from './components/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { ClientesPage } from './pages/ClientesPage'
import { ClienteDetailPage } from './pages/ClienteDetailPage'
import { DeParaPage } from './pages/DeParaPage'

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/clientes"
          element={
            <ProtectedRoute>
              <AppLayout>
                <ClientesPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/clientes/:clienteId"
          element={
            <ProtectedRoute>
              <AppLayout>
                <ClienteDetailPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/de-para"
          element={
            <ProtectedRoute>
              <AppLayout>
                <DeParaPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/clientes" replace />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
