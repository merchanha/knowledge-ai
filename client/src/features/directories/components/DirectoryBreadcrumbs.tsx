import { Folder } from 'lucide-react'
import { Link } from 'react-router-dom'

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import { useBreadcrumbs } from '@/features/directories/hooks/use-directory-tree'

interface DirectoryBreadcrumbsProps {
  projectId: string
  directoryId: string | undefined
}

export function DirectoryBreadcrumbs({
  projectId,
  directoryId,
}: DirectoryBreadcrumbsProps) {
  const { data = [], isLoading } = useBreadcrumbs(directoryId)

  if (!directoryId) {
    return null
  }

  if (isLoading) {
    return (
      <p className="text-sm text-muted-foreground">Loading path…</p>
    )
  }

  return (
    <Breadcrumb>
      <BreadcrumbList>
        {data.map((dir, index) => {
          const isLast = index === data.length - 1
          return (
            <BreadcrumbItem key={dir.id} className="contents">
              {index > 0 ? <BreadcrumbSeparator /> : null}
              {isLast ? (
                <BreadcrumbPage className="inline-flex items-center gap-1.5">
                  <Folder className="size-3.5 opacity-70" />
                  {dir.name}
                </BreadcrumbPage>
              ) : (
                <BreadcrumbLink asChild>
                  <Link
                    to={`/projects/${projectId}/directories/${dir.id}`}
                    className="inline-flex items-center gap-1.5"
                  >
                    {index === 0 ? (
                      <Folder className="size-3.5 opacity-70" />
                    ) : null}
                    {dir.name}
                  </Link>
                </BreadcrumbLink>
              )}
            </BreadcrumbItem>
          )
        })}
      </BreadcrumbList>
    </Breadcrumb>
  )
}
