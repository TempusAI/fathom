'use client'

import { useState } from 'react'
import { ChevronRight, ChevronDown, Calendar, AlertCircle, CheckCircle2, Clock, Users } from 'lucide-react'
import { format } from 'date-fns'
import { TaskGroup } from '@/types/tasks'
import { usePlaygroundStore } from '@/store'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'
import { TaskItem } from './TaskItem'

interface TaskGroupItemProps {
  group: TaskGroup
}

function getStateIcon(state: string) {
  switch (state.toLowerCase()) {
    case 'completed':
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    case 'inreview':
    case 'in review':
      return <AlertCircle className="h-4 w-4 text-yellow-500" />
    case 'pending':
      return <Clock className="h-4 w-4 text-blue-500" />
    case 'resolved':
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    case 'searching errors':
      return <AlertCircle className="h-4 w-4 text-orange-500" />
    default:
      return <AlertCircle className="h-4 w-4 text-gray-500" />
  }
}

function getStateVariant(state: string): "default" | "secondary" | "destructive" | "outline" {
  switch (state.toLowerCase()) {
    case 'completed':
    case 'resolved':
      return 'default'
    case 'inreview':
    case 'in review':
      return 'secondary'
    case 'pending':
      return 'outline'
    default:
      return 'secondary'
  }
}

export function TaskGroupItem({ group }: TaskGroupItemProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const { selectedTasks, addSelectedTaskGroup, removeSelectedTaskGroup } = usePlaygroundStore()
  
  const { ultimateParent, children, totalCount } = group
  
  // Check if this group is selected (all tasks from group are selected)
  const isGroupSelected = selectedTasks.some(task => task.id === ultimateParent.id) &&
    children.every(child => selectedTasks.some(task => task.id === child.id))

  const createdDate = new Date(ultimateParent.version.asAtCreated)

  const handleGroupSelect = () => {
    if (isGroupSelected) {
      removeSelectedTaskGroup(ultimateParent.id)
    } else {
      addSelectedTaskGroup(group)
    }
  }

  return (
    <Card className={cn(
      "transition-all duration-200 hover:shadow-md border-border/30",
      isGroupSelected && "ring-1 ring-primary/30 bg-primary/5"
    )}>
      <CardContent className="p-3">
        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          {/* Ultimate Parent Header */}
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <CollapsibleTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="p-1 h-5 w-5 text-muted-foreground hover:text-foreground"
                  disabled={children.length === 0}
                >
                  {children.length > 0 ? (
                    isExpanded ? (
                      <ChevronDown className="h-3 w-3" />
                    ) : (
                      <ChevronRight className="h-3 w-3" />
                    )
                  ) : (
                    <div className="h-3 w-3" />
                  )}
                </Button>
              </CollapsibleTrigger>

              {getStateIcon(ultimateParent.state)}
              
              <div className="min-w-0 flex-1">
                <h4 className="font-medium text-sm truncate text-foreground">
                  {ultimateParent.taskDefinitionDisplayName}
                </h4>
              </div>
              
              <Badge variant={getStateVariant(ultimateParent.state)} className="text-xs shrink-0">
                {ultimateParent.state}
              </Badge>
              
              {children.length > 0 && (
                <div className="flex items-center gap-1 text-xs text-muted-foreground shrink-0">
                  <Users className="h-3 w-3" />
                  <span>{children.length}</span>
                </div>
              )}
              
              <div className="flex items-center gap-1 text-xs text-muted-foreground shrink-0">
                <Calendar className="h-3 w-3" />
                <span>{format(createdDate, 'MMM d')}</span>
              </div>
              
              <Button
                size="sm"
                variant={isGroupSelected ? "secondary" : "outline"}
                className="text-xs px-3 shrink-0"
                onClick={handleGroupSelect}
              >
                {isGroupSelected ? 'Selected' : 'Select Group'}
              </Button>
            </div>
          </div>

          {/* Child Tasks */}
          {children.length > 0 && (
            <CollapsibleContent className="space-y-2 mt-3 pl-6">
              <div className="border-l-2 border-border/20 pl-4 space-y-2">
                {children.map((child) => (
                  <TaskItem key={child.id} task={child} isChild />
                ))}
              </div>
            </CollapsibleContent>
          )}
        </Collapsible>
      </CardContent>
    </Card>
  )
}
