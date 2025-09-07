'use client'

import { useEffect } from 'react'
import { usePlaygroundStore } from '@/store'
import { getMockTaskGroups } from '@/lib/mockTasks'
import { DateFilter } from './DateFilter'
import { TaskList } from './TaskList'
import { SearchFilter } from './SearchFilter'
import { Separator } from '@/components/ui/separator'

export function TaskPanel() {
  const { 
    taskGroups, 
    setTaskGroups, 
    taskFilter,
    isTaskPanelVisible 
  } = usePlaygroundStore()

  // Load mock data on mount
  useEffect(() => {
    const mockGroups = getMockTaskGroups()
    setTaskGroups(mockGroups)
  }, [setTaskGroups])

  if (!isTaskPanelVisible) {
    return null
  }

  // Filter task groups based on current filters
  const filteredGroups = taskGroups.filter(group => {
    // Date filter
    if (taskFilter.dateFrom || taskFilter.dateTo) {
      const createdDate = new Date(group.ultimateParent.version.asAtCreated)
      if (taskFilter.dateFrom && createdDate < new Date(taskFilter.dateFrom)) {
        return false
      }
      if (taskFilter.dateTo && createdDate > new Date(taskFilter.dateTo)) {
        return false
      }
    }

    // Search filter
    if (taskFilter.searchQuery) {
      const query = taskFilter.searchQuery.toLowerCase()
      const parentMatches = group.ultimateParent.taskDefinitionDisplayName.toLowerCase().includes(query) ||
                           group.ultimateParent.state.toLowerCase().includes(query)
      const childMatches = group.children.some(child => 
        child.taskDefinitionDisplayName.toLowerCase().includes(query) ||
        child.state.toLowerCase().includes(query)
      )
      if (!parentMatches && !childMatches) {
        return false
      }
    }

    // State filter
    if (taskFilter.states && taskFilter.states.length > 0) {
      const parentStateMatches = taskFilter.states.includes(group.ultimateParent.state as any)
      const childStateMatches = group.children.some(child => 
        taskFilter.states!.includes(child.state as any)
      )
      if (!parentStateMatches && !childStateMatches) {
        return false
      }
    }

    return true
  })

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex flex-col gap-4 p-6">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-foreground">
            Aggregation Error Tasks
          </h2>
          <p className="text-sm text-muted-foreground mt-2">
            Select tasks to investigate data quality issues
          </p>
        </div>
        
        <Separator className="bg-border/30" />
        
        {/* Filters */}
        <div className="flex gap-3">
          <div className="flex-1">
            <DateFilter />
          </div>
          <div className="flex-1">
            <SearchFilter />
          </div>
        </div>
      </div>

      {/* Task List */}
      <div className="flex-1 overflow-hidden">
        <TaskList groups={filteredGroups} />
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-border/30">
        <p className="text-xs text-muted-foreground text-center">
          {filteredGroups.length} task group{filteredGroups.length !== 1 ? 's' : ''} • 
          {filteredGroups.reduce((sum, group) => sum + group.totalCount, 0)} total tasks
        </p>
      </div>
    </div>
  )
}
