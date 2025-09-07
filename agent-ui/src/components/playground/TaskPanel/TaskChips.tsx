'use client'

import { X, Database, TrendingUp } from 'lucide-react'
import { usePlaygroundStore } from '@/store'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

export function TaskChips() {
  const { selectedTasks, removeSelectedTask, taskGroups } = usePlaygroundStore()

  if (selectedTasks.length === 0) {
    return null
  }

  // Group selected tasks by ultimate parent for better display
  const groupedTasks = selectedTasks.reduce((acc, task) => {
    const ultimateParentId = task.ultimateParentTask?.id || task.id
    if (!acc[ultimateParentId]) {
      acc[ultimateParentId] = []
    }
    acc[ultimateParentId].push(task)
    return acc
  }, {} as Record<string, typeof selectedTasks>)

  return (
    <div className="border-t border-border/30 bg-background/50 p-3">
      <div className="flex items-center gap-2 mb-2">
        <div className="text-xs font-medium text-muted-foreground">
          Selected Tasks ({selectedTasks.length})
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-5 px-2 text-xs text-muted-foreground hover:text-foreground"
          onClick={() => {
            selectedTasks.forEach(task => removeSelectedTask(task.id))
          }}
        >
          Clear all
        </Button>
      </div>
      
      <ScrollArea className="max-h-32">
        <div className="flex flex-wrap gap-2">
          {Object.entries(groupedTasks).map(([ultimateParentId, tasks]) => {
            const isGroup = tasks.length > 1
            const ultimateParent = tasks.find(t => t.id === ultimateParentId) || tasks[0]
            
            if (isGroup) {
              // Show group chip
              return (
                <GroupChip
                  key={ultimateParentId}
                  ultimateParent={ultimateParent}
                  childCount={tasks.length - 1}
                  onRemove={() => {
                    tasks.forEach(task => removeSelectedTask(task.id))
                  }}
                />
              )
            } else {
              // Show individual task chip
              const task = tasks[0]
              return (
                <TaskChip
                  key={task.id}
                  task={task}
                  onRemove={() => removeSelectedTask(task.id)}
                />
              )
            }
          })}
        </div>
      </ScrollArea>
    </div>
  )
}

interface TaskChipProps {
  task: any
  onRemove: () => void
}

function TaskChip({ task, onRemove }: TaskChipProps) {
  const portfolioCode = task.fields?.find((f: any) => f.name === 'PortfolioCode')?.value
  const ticker = task.fields?.find((f: any) => f.name === 'Ticker')?.value
  
  return (
    <Badge
      variant="secondary"
      className={cn(
        "flex items-center gap-2 pr-1 max-w-xs",
        "hover:bg-secondary/80 transition-colors"
      )}
    >
      <div className="flex items-center gap-1 min-w-0 flex-1">
        {portfolioCode && (
          <div className="flex items-center gap-1">
            <Database className="h-3 w-3 text-muted-foreground" />
            <span className="text-xs">{portfolioCode}</span>
          </div>
        )}
        {ticker && (
          <div className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3 text-muted-foreground" />
            <span className="text-xs font-medium">{ticker}</span>
          </div>
        )}
        {!portfolioCode && !ticker && (
          <span className="text-xs truncate">
            {task.taskDefinitionDisplayName}
          </span>
        )}
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="h-4 w-4 p-0 hover:bg-destructive hover:text-destructive-foreground"
        onClick={onRemove}
      >
        <X className="h-3 w-3" />
      </Button>
    </Badge>
  )
}

interface GroupChipProps {
  ultimateParent: any
  childCount: number
  onRemove: () => void
}

function GroupChip({ ultimateParent, childCount, onRemove }: GroupChipProps) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "flex items-center gap-2 pr-1 border-primary/30 bg-primary/5",
        "hover:bg-primary/10 transition-colors"
      )}
    >
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium truncate max-w-[120px]">
          {ultimateParent.taskDefinitionDisplayName}
        </span>
        <div className="flex items-center gap-1 px-1.5 py-0.5 bg-primary/20 rounded text-xs">
          <span>{childCount + 1} tasks</span>
        </div>
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="h-4 w-4 p-0 hover:bg-destructive hover:text-destructive-foreground"
        onClick={onRemove}
      >
        <X className="h-3 w-3" />
      </Button>
    </Badge>
  )
}
