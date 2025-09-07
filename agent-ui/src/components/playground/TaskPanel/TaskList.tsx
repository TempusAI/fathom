'use client'

import { TaskGroup } from '@/types/tasks'
import { TaskGroupItem } from './TaskGroupItem'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'

interface TaskListProps {
  groups: TaskGroup[]
  isLoading?: boolean
}

function TaskSkeleton() {
  return (
    <div className="border rounded-md border-border/30">
      <div className="p-3 flex items-center gap-3">
        <Skeleton className="h-3 w-3 rounded-full" />
        <div className="flex-1 min-w-0">
          <Skeleton className="h-4 w-48" />
        </div>
        <Skeleton className="h-4 w-16" />
      </div>
    </div>
  )
}

export function TaskList({ groups, isLoading }: TaskListProps) {
  // Show skeleton only on initial load (when no data yet). During background fetches keep the list visible.
  if (isLoading && groups.length === 0) {
    return (
      <ScrollArea className="h-full">
        <div className="space-y-2 p-4">
          <TaskSkeleton />
        </div>
      </ScrollArea>
    )
  }
  if (groups.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <div className="text-center">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-lg font-medium text-foreground mb-2">
            No tasks found
          </h3>
          <p className="text-sm text-muted-foreground">
            Try adjusting your filters or check back later
          </p>
        </div>
      </div>
    )
  }

  return (
    <ScrollArea className="h-full">
      <div className="space-y-2 p-4">
        {groups.map((group) => (
          <TaskGroupItem key={group.ultimateParent.id} group={group} />
        ))}
      </div>
    </ScrollArea>
  )
}
