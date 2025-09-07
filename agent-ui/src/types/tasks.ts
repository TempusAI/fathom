// LUSID Workflow Task Types - Based on real API responses

export interface TaskDefinitionId {
  scope: string
  code: string
}

export interface TaskDefinitionVersion {
  asAtModified: string
}

export interface TaskVersion {
  asAtCreated: string
  userIdCreated: string
  requestIdCreated: string
  asAtModified: string
  userIdModified: string
  requestIdModified: string
  asAtVersionNumber: number
}

export interface TaskField {
  name: string
  value: string | number | null
}

export interface TaskReference {
  id: string
  taskDefinitionId: TaskDefinitionId
  taskDefinitionVersion: TaskDefinitionVersion
  taskDefinitionDisplayName: string
  state: string
}

export interface WorkflowTask {
  id: string
  taskDefinitionId: TaskDefinitionId
  taskDefinitionVersion: TaskDefinitionVersion
  taskDefinitionDisplayName: string
  state: TaskState
  ultimateParentTask?: TaskReference
  parentTask?: TaskReference
  childTasks: TaskReference[]
  correlationIds: string[]
  version: TaskVersion
  terminalState: boolean
  asAtLastTransition: string
  fields: TaskField[]
  stackingKey?: string
  actionLogIdCreated?: string
  actionLogIdModified?: string
  actionLogIdSubmitted?: string
}

// Aggregation Error specific states
export type UltimateParentState = 'Pending' | 'Searching Errors' | 'inReview' | 'Completed'
export type ChildTaskState = 'Pending' | 'InReview' | 'Resolved'
export type TaskState = UltimateParentState | ChildTaskState

export interface TaskListResponse {
  nextPage?: string
  previousPage?: string
  values: WorkflowTask[]
  href: string
  links: Array<{
    relation: string
    href: string
    description: string
    method: string
  }>
}

// UI-specific types
export interface TaskGroup {
  ultimateParent: WorkflowTask
  children: WorkflowTask[]
  totalCount: number
}

export interface TaskFilter {
  dateFrom?: string
  dateTo?: string
  searchQuery?: string
  states?: TaskState[]
  correlationIds?: string[]
}

// Store interface extension
export interface TaskStore {
  selectedTasks: WorkflowTask[]
  taskGroups: TaskGroup[]
  taskFilter: TaskFilter
  isTaskPanelVisible: boolean
  
  // Actions
  addSelectedTask: (task: WorkflowTask) => void
  removeSelectedTask: (taskId: string) => void
  addSelectedTaskGroup: (group: TaskGroup) => void
  removeSelectedTaskGroup: (ultimateParentId: string) => void
  setTaskFilter: (filter: Partial<TaskFilter>) => void
  setTaskGroups: (groups: TaskGroup[]) => void
  clearSelectedTasks: () => void
  setTaskPanelVisible: (visible: boolean) => void
}
