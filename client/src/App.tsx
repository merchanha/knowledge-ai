import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { AccountPage } from '@/features/account/pages/AccountPage'
import { UsersPage } from '@/features/admin/pages/UsersPage'
import { AdminRoute } from '@/features/auth/components/AdminRoute'
import { ProtectedRoute } from '@/features/auth/components/ProtectedRoute'
import { AuthCallbackPage } from '@/features/auth/pages/AuthCallbackPage'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { CommandsPage } from '@/features/commands/pages/CommandsPage'
import { DirectoriesPage } from '@/features/directories/pages/DirectoriesPage'
import { KnowledgeNeuronsPage } from '@/features/knowledge-neurons/pages/KnowledgeNeuronsPage'
import { ProjectDetailPage } from '@/features/projects/pages/ProjectDetailPage'
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
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route
            path="/projects/:projectId/directories"
            element={<DirectoriesPage />}
          />
          <Route
            path="/projects/:projectId/directories/:directoryId"
            element={<DirectoriesPage />}
          />

          <Route path="/knowledge" element={<KnowledgeNeuronsPage />} />
          <Route
            path="/knowledge/projects/:projectId"
            element={<KnowledgeNeuronsPage />}
          />
          <Route
            path="/knowledge/projects/:projectId/directories/:directoryId"
            element={<KnowledgeNeuronsPage />}
          />

          <Route path="/commands" element={<CommandsPage />} />
          <Route
            path="/commands/projects/:projectId"
            element={<CommandsPage />}
          />
          <Route
            path="/commands/projects/:projectId/directories/:directoryId"
            element={<CommandsPage />}
          />

          <Route path="/account" element={<AccountPage />} />

          <Route element={<AdminRoute />}>
            <Route path="/users" element={<UsersPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/projects" replace />} />
    </Routes>
  )
}
