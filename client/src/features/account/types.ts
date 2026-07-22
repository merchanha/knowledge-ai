export type ProjectMembershipRole = 'owner' | 'member'

export interface AccountProject {
  id: string
  name: string
  description: string | null
  is_archived: boolean
  membership_role: ProjectMembershipRole
  is_context_exposed: boolean
}

export interface Membership {
  id: string
  user_id: string
  project_id: string
  role: ProjectMembershipRole
  is_context_exposed: boolean
  created_at: string
  updated_at: string
}
