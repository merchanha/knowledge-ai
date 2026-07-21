import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { ProtectedRoute } from '@/features/auth/components/ProtectedRoute'
import { AuthCallbackPage } from '@/features/auth/pages/AuthCallbackPage'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { DirectoriesPage } from '@/features/directories/pages/DirectoriesPage'
import { ProjectsPage } from '@/features/projects/pages/ProjectsPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<Navigate to="/projects" replace />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route
            path="/projects/:projectId/directories"
            element={<DirectoriesPage />}
          />
          <Route
            path="/projects/:projectId/directories/:directoryId"
            element={<DirectoriesPage />}
          />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/projects" replace />} />
    </Routes>
  )
}
