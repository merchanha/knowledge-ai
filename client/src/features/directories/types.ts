export interface Directory {
  id: string
  project_id: string
  parent_id: string | null
  name: string
  is_root: boolean
}

export type DirectoryPermission = 'READ' | 'WRITE' | 'MANAGE'

export interface DirectoryPermissionEntry {
  directory_id: string
  permission: DirectoryPermission
}

export interface DirectoryTreeNode extends Directory {
  children: DirectoryTreeNode[]
}
