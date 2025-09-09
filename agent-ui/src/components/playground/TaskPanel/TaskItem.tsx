'use client'

import { format } from 'date-fns'
import { Calendar, AlertCircle, CheckCircle2, Clock, Database, TrendingUp } from 'lucide-react'
import { WorkflowTask } from '@/types/tasks'
import { usePlaygroundStore } from '@/store'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

interface TaskItemProps {
  task: WorkflowTask
  isChild?: boolean
}

function getStateIcon(state: string) {
  switch (state.toLowerCase()) {
    case 'completed':
      return <CheckCircle2 className="h-3 w-3 text-green-500" />
    case 'inreview':
    case 'in review':
      return <AlertCircle className="h-3 w-3 text-yellow-500" />
    case 'pending':
      return <Clock className="h-3 w-3 text-blue-500" />
    case 'resolved':
      return <CheckCircle2 className="h-3 w-3 text-green-500" />
    default:
      return <AlertCircle className="h-3 w-3 text-gray-500" />
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

export function TaskItem({ task, isChild = false }: TaskItemProps) {
  const { selectedTasks, addSelectedTask, removeSelectedTask } = usePlaygroundStore()
  
  const isSelected = selectedTasks.some(t => t.id === task.id)
  const createdDate = new Date(task.version.asAtCreated)

  // Extract key fields for display
  const portfolioCode = task.fields.find(f => f.name === 'PortfolioCode')?.value
  const instrumentName = task.fields.find(f => f.name === 'Name')?.value
  const ticker = task.fields.find(f => f.name === 'Ticker')?.value
  const errorMessage = task.fields.find(f => f.name === 'Error')?.value

  const handleSelect = () => {
    if (isSelected) {
      removeSelectedTask(task.id)
    } else {
      addSelectedTask(task)
    }
  }

  const CardComponent = isChild ? 'div' : Card

  return (
    <CardComponent className={cn(
      isChild ? "border border-border/20 rounded-md bg-background/40" : "",
      "transition-all duration-200 hover:shadow-sm",
      isSelected && "ring-1 ring-primary/30 bg-primary/5"
    )}>
      <CardContent className={cn("p-3", !isChild && "")}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2 flex-1 min-w-0">
            {getStateIcon(task.state)}
            
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h5 className="text-sm font-medium truncate">
                  {task.taskDefinitionDisplayName}
                </h5>
                <Badge variant={getStateVariant(task.state)} className="text-xs">
                  {task.state}
                </Badge>
              </div>

              {/* Task Details */}
              <div className="space-y-1">
                {portfolioCode && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Database className="h-3 w-3" />
                    Portfolio: {portfolioCode}
                  </div>
                )}
                
                {(instrumentName || ticker) && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <TrendingUp className="h-3 w-3" />
                    {ticker ? `${ticker}${instrumentName ? ` (${instrumentName})` : ''}` : instrumentName}
                  </div>
                )}

                {errorMessage && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="text-xs text-red-600 dark:text-red-400 truncate cursor-help">
                        Error: {String(errorMessage).substring(0, 60)}...
                      </div>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-md">
                      <p className="text-sm">{errorMessage}</p>
                    </TooltipContent>
                  </Tooltip>
                )}

                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3" />
                  {format(createdDate, 'MMM d, HH:mm')}
                </div>
              </div>
            </div>
          </div>

          <Button
            size="sm"
            variant={isSelected ? "ghost" : "outline"}
            className={cn(
              "text-xs px-2 shrink-0",
              isSelected && "text-muted-foreground hover:text-muted-foreground"
            )}
            onClick={handleSelect}
          >
            {isSelected ? 'Deselect' : 'Select'}
          </Button>
        </div>
      </CardContent>
    </CardComponent>
  )
}
