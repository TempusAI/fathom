'use client'

import { TaskGroup } from '@/types/tasks'
import { TaskGroupItem } from './TaskGroupItem'
import { ScrollArea } from '@/components/ui/scroll-area'

interface TaskListProps {
  groups: TaskGroup[]
}

export function TaskList({ groups }: TaskListProps) {
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
