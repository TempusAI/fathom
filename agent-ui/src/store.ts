import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

import {
  type PlaygroundChatMessage,
  type SessionEntry
} from '@/types/playground'
import { 
  type WorkflowTask, 
  type TaskGroup, 
  type TaskFilter 
} from '@/types/tasks'

interface Agent {
  value: string
  label: string
  model: {
    provider: string
  }
  storage?: boolean
}

export interface Team {
  value: string
  label: string
  model: {
    provider: string
  }
  storage?: boolean
}

interface PlaygroundStore {
  hydrated: boolean
  setHydrated: () => void
  streamingErrorMessage: string
  setStreamingErrorMessage: (streamingErrorMessage: string) => void
  endpoints: {
    endpoint: string
    id_playground_endpoint: string
  }[]
  setEndpoints: (
    endpoints: {
      endpoint: string
      id_playground_endpoint: string
    }[]
  ) => void
  isStreaming: boolean
  setIsStreaming: (isStreaming: boolean) => void
  isEndpointActive: boolean
  setIsEndpointActive: (isActive: boolean) => void
  isEndpointLoading: boolean
  setIsEndpointLoading: (isLoading: boolean) => void
  messages: PlaygroundChatMessage[]
  setMessages: (
    messages:
      | PlaygroundChatMessage[]
      | ((prevMessages: PlaygroundChatMessage[]) => PlaygroundChatMessage[])
  ) => void
  hasStorage: boolean
  setHasStorage: (hasStorage: boolean) => void
  chatInputRef: React.RefObject<HTMLTextAreaElement | null>
  selectedEndpoint: string
  setSelectedEndpoint: (selectedEndpoint: string) => void
  agents: Agent[]
  setAgents: (agents: Agent[]) => void
  teams: Team[]
  setTeams: (teams: Team[]) => void
  selectedModel: string
  setSelectedModel: (model: string) => void
  selectedTeamId: string | null
  setSelectedTeamId: (teamId: string | null) => void
  mode: 'agent' | 'team'
  setMode: (mode: 'agent' | 'team') => void
  sessionsData: SessionEntry[] | null
  setSessionsData: (
    sessionsData:
      | SessionEntry[]
      | ((prevSessions: SessionEntry[] | null) => SessionEntry[] | null)
  ) => void
  isSessionsLoading: boolean
  setIsSessionsLoading: (isSessionsLoading: boolean) => void
  
  // Task management
  selectedTasks: WorkflowTask[]
  taskGroups: TaskGroup[]
  taskFilter: TaskFilter
  isTaskPanelVisible: boolean
  
  // Task actions
  addSelectedTask: (task: WorkflowTask) => void
  removeSelectedTask: (taskId: string) => void
  addSelectedTaskGroup: (group: TaskGroup) => void
  removeSelectedTaskGroup: (ultimateParentId: string) => void
  setTaskFilter: (filter: Partial<TaskFilter>) => void
  setTaskGroups: (groups: TaskGroup[]) => void
  clearSelectedTasks: () => void
  setTaskPanelVisible: (visible: boolean) => void
}

export const usePlaygroundStore = create<PlaygroundStore>()(
  persist(
    (set) => ({
      hydrated: false,
      setHydrated: () => set({ hydrated: true }),
      streamingErrorMessage: '',
      setStreamingErrorMessage: (streamingErrorMessage) =>
        set(() => ({ streamingErrorMessage })),
      endpoints: [],
      setEndpoints: (endpoints) => set(() => ({ endpoints })),
      isStreaming: false,
      setIsStreaming: (isStreaming) => set(() => ({ isStreaming })),
      isEndpointActive: false,
      setIsEndpointActive: (isActive) =>
        set(() => ({ isEndpointActive: isActive })),
      isEndpointLoading: true,
      setIsEndpointLoading: (isLoading) =>
        set(() => ({ isEndpointLoading: isLoading })),
      messages: [],
      setMessages: (messages) =>
        set((state) => ({
          messages:
            typeof messages === 'function' ? messages(state.messages) : messages
        })),
      hasStorage: false,
      setHasStorage: (hasStorage) => set(() => ({ hasStorage })),
      chatInputRef: { current: null },
      selectedEndpoint: 'http://localhost:7777',
      setSelectedEndpoint: (selectedEndpoint) =>
        set(() => ({ selectedEndpoint })),
      agents: [],
      setAgents: (agents) => set({ agents }),
      teams: [],
      setTeams: (teams) => set({ teams }),
      selectedModel: '',
      setSelectedModel: (selectedModel) => set(() => ({ selectedModel })),
      selectedTeamId: null,
      setSelectedTeamId: (teamId) => set(() => ({ selectedTeamId: teamId })),
      mode: 'team',
      setMode: (mode) => set(() => ({ mode })),
      sessionsData: null,
      setSessionsData: (sessionsData) =>
        set((state) => ({
          sessionsData:
            typeof sessionsData === 'function'
              ? sessionsData(state.sessionsData)
              : sessionsData
        })),
      isSessionsLoading: false,
      setIsSessionsLoading: (isSessionsLoading) =>
        set(() => ({ isSessionsLoading })),
      
      // Task management state
      selectedTasks: [],
      taskGroups: [],
      taskFilter: {},
      isTaskPanelVisible: true,
      
      // Task actions
      addSelectedTask: (task) =>
        set((state) => ({
          selectedTasks: [...state.selectedTasks.filter(t => t.id !== task.id), task]
        })),
      removeSelectedTask: (taskId) =>
        set((state) => ({
          selectedTasks: state.selectedTasks.filter(t => t.id !== taskId)
        })),
      addSelectedTaskGroup: (group) =>
        set((state) => ({
          selectedTasks: [
            ...state.selectedTasks.filter(t => 
              t.id !== group.ultimateParent.id && 
              !group.children.some(child => child.id === t.id)
            ),
            group.ultimateParent,
            ...group.children
          ]
        })),
      removeSelectedTaskGroup: (ultimateParentId) =>
        set((state) => {
          const group = state.taskGroups.find(g => g.ultimateParent.id === ultimateParentId)
          if (!group) return state
          
          const childIds = group.children.map(c => c.id)
          return {
            selectedTasks: state.selectedTasks.filter(t => 
              t.id !== ultimateParentId && !childIds.includes(t.id)
            )
          }
        }),
      setTaskFilter: (filter) =>
        set((state) => ({
          taskFilter: { ...state.taskFilter, ...filter }
        })),
      setTaskGroups: (groups) =>
        set(() => ({ taskGroups: groups })),
      clearSelectedTasks: () =>
        set(() => ({ selectedTasks: [] })),
      setTaskPanelVisible: (visible) =>
        set(() => ({ isTaskPanelVisible: visible }))
    }),
    {
      name: 'endpoint-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        selectedEndpoint: state.selectedEndpoint
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated?.()
      }
    }
  )
)
