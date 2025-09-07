// Mock data based on real LUSID Aggregation Error API responses

import { WorkflowTask, TaskGroup, TaskListResponse } from '@/types/tasks'

export const mockTasks: WorkflowTask[] = [
  // Ultimate Parent Task 1 - with multiple children
  {
    id: '2b888027-60e4-405e-82c6-bc0be9493e2e',
    taskDefinitionId: {
      scope: 'IBOR-DQ-ProdTeam',
      code: 'IBOR-DQ-Parent-Aggregation-Errors'
    },
    taskDefinitionVersion: {
      asAtModified: '2025-07-24T04:42:11.1130120+00:00'
    },
    taskDefinitionDisplayName: 'Aggregation Errors Parent Task',
    state: 'inReview',
    childTasks: [
      {
        id: '0006c6c2-a96a-4c4b-a283-549cb7b56998',
        taskDefinitionId: {
          scope: 'IBOR-DQ-ProdTeam',
          code: 'IBOR-DQ-Child-Aggregation-Error-Check'
        },
        taskDefinitionVersion: {
          asAtModified: '2025-07-24T04:42:09.9825630+00:00'
        },
        taskDefinitionDisplayName: 'Aggregation Errors Exception',
        state: 'InReview'
      },
      {
        id: '1234c6c2-a96a-4c4b-a283-549cb7b56998',
        taskDefinitionId: {
          scope: 'IBOR-DQ-ProdTeam',
          code: 'IBOR-DQ-Child-Aggregation-Error-Check'
        },
        taskDefinitionVersion: {
          asAtModified: '2025-07-24T04:42:09.9825630+00:00'
        },
        taskDefinitionDisplayName: 'Aggregation Errors Exception',
        state: 'Pending'
      },
      {
        id: '5678c6c2-a96a-4c4b-a283-549cb7b56998',
        taskDefinitionId: {
          scope: 'IBOR-DQ-ProdTeam',
          code: 'IBOR-DQ-Child-Aggregation-Error-Check'
        },
        taskDefinitionVersion: {
          asAtModified: '2025-07-24T04:42:09.9825630+00:00'
        },
        taskDefinitionDisplayName: 'Aggregation Errors Exception',
        state: 'Resolved'
      }
    ],
    correlationIds: ['Early Morning DQ'],
    version: {
      asAtCreated: '2025-09-01T22:44:18.5067730+00:00',
      userIdCreated: '00u12u680zegmCPd62p8',
      requestIdCreated: 'requestId',
      asAtModified: '2025-09-01T22:44:18.5067730+00:00',
      userIdModified: '00u12u680zegmCPd62p8',
      requestIdModified: 'requestId',
      asAtVersionNumber: 1
    },
    terminalState: false,
    asAtLastTransition: '2025-09-01T22:44:18.5067730+00:00',
    fields: [],
    actionLogIdCreated: '579bb58f-95b0-46ec-a834-3af2a2506a28',
    actionLogIdModified: '579bb58f-95b0-46ec-a834-3af2a2506a28'
  },

  // Child Task 1
  {
    id: '0006c6c2-a96a-4c4b-a283-549cb7b56998',
    taskDefinitionId: {
      scope: 'IBOR-DQ-ProdTeam',
      code: 'IBOR-DQ-Child-Aggregation-Error-Check'
    },
    taskDefinitionVersion: {
      asAtModified: '2025-07-24T04:42:09.9825630+00:00'
    },
    taskDefinitionDisplayName: 'Aggregation Errors Exception',
    state: 'InReview',
    ultimateParentTask: {
      id: '2b888027-60e4-405e-82c6-bc0be9493e2e',
      taskDefinitionId: {
        scope: 'IBOR-DQ-ProdTeam',
        code: 'IBOR-DQ-Parent-Aggregation-Errors'
      },
      taskDefinitionVersion: {
        asAtModified: '2025-07-24T04:42:11.1130120+00:00'
      },
      taskDefinitionDisplayName: 'Aggregation Errors Parent Task',
      state: 'inReview'
    },
    parentTask: {
      id: '2b888027-60e4-405e-82c6-bc0be9493e2e',
      taskDefinitionId: {
        scope: 'IBOR-DQ-ProdTeam',
        code: 'IBOR-DQ-Parent-Aggregation-Errors'
      },
      taskDefinitionVersion: {
        asAtModified: '2025-07-24T04:42:11.1130120+00:00'
      },
      taskDefinitionDisplayName: 'Aggregation Errors Parent Task',
      state: 'inReview'
    },
    childTasks: [],
    correlationIds: ['Early Morning DQ'],
    version: {
      asAtCreated: '2025-09-01T22:44:18.5067730+00:00',
      userIdCreated: '00u12u680zegmCPd62p8',
      requestIdCreated: 'requestId',
      asAtModified: '2025-09-01T22:44:18.5067730+00:00',
      userIdModified: '00u12u680zegmCPd62p8',
      requestIdModified: 'requestId',
      asAtVersionNumber: 1
    },
    terminalState: false,
    asAtLastTransition: '2025-09-01T22:44:18.5067730+00:00',
    fields: [
      {
        name: 'ValuationDate',
        value: '09/01/2025 08:42:07'
      },
      {
        name: 'PortfolioCode',
        value: 'ARMO'
      },
      {
        name: 'LusidInstrumentId',
        value: 'LUID_00003J8G'
      },
      {
        name: 'Error',
        value: "One of the measures in the columns + requested measures errored with: Failed to resolve market data for economic dependency 'Quote:{ {LusidInstrumentId: LUID_00003J8G}, {RIC: JRV.AX}, {Isin: AU000000JRV4}, {Sedol: 6473015} }:2025-08-31T22:42:07.0000000+00:00' as-at '2025-08-31T22:42:01.0153510+00:00'."
      },
      {
        name: 'BlackRockAladdinID',
        value: 'S64730153'
      },
      {
        name: 'Name',
        value: 'JERVOIS GLOBAL LTD'
      },
      {
        name: 'InstrumentType',
        value: 'Equity'
      },
      {
        name: 'DomCcy',
        value: 'AUD'
      },
      {
        name: 'Units',
        value: '625646101'
      },
      {
        name: 'Ticker',
        value: 'JRV'
      },
      {
        name: 'RIC',
        value: 'JRV.AX'
      },
      {
        name: 'SEDOL',
        value: '6473015'
      },
      {
        name: 'ISIN',
        value: 'AU000000JRV4'
      }
    ],
    actionLogIdCreated: '579bb58f-95b0-46ec-a834-3af2a2506a28',
    actionLogIdModified: '579bb58f-95b0-46ec-a834-3af2a2506a28'
  },

  // Child Task 2
  {
    id: '1234c6c2-a96a-4c4b-a283-549cb7b56998',
    taskDefinitionId: {
      scope: 'IBOR-DQ-ProdTeam',
      code: 'IBOR-DQ-Child-Aggregation-Error-Check'
    },
    taskDefinitionVersion: {
      asAtModified: '2025-07-24T04:42:09.9825630+00:00'
    },
    taskDefinitionDisplayName: 'Aggregation Errors Exception',
    state: 'Pending',
    ultimateParentTask: {
      id: '2b888027-60e4-405e-82c6-bc0be9493e2e',
      taskDefinitionId: {
        scope: 'IBOR-DQ-ProdTeam',
        code: 'IBOR-DQ-Parent-Aggregation-Errors'
      },
      taskDefinitionVersion: {
        asAtModified: '2025-07-24T04:42:11.1130120+00:00'
      },
      taskDefinitionDisplayName: 'Aggregation Errors Parent Task',
      state: 'inReview'
    },
    parentTask: {
      id: '2b888027-60e4-405e-82c6-bc0be9493e2e',
      taskDefinitionId: {
        scope: 'IBOR-DQ-ProdTeam',
        code: 'IBOR-DQ-Parent-Aggregation-Errors'
      },
      taskDefinitionVersion: {
        asAtModified: '2025-07-24T04:42:11.1130120+00:00'
      },
      taskDefinitionDisplayName: 'Aggregation Errors Parent Task',
      state: 'inReview'
    },
    childTasks: [],
    correlationIds: ['Early Morning DQ'],
    version: {
      asAtCreated: '2025-09-02T14:30:22.1234567+00:00',
      userIdCreated: '00u12u680zegmCPd62p8',
      requestIdCreated: 'requestId',
      asAtModified: '2025-09-02T14:30:22.1234567+00:00',
      userIdModified: '00u12u680zegmCPd62p8',
      requestIdModified: 'requestId',
      asAtVersionNumber: 1
    },
    terminalState: false,
    asAtLastTransition: '2025-09-02T14:30:22.1234567+00:00',
    fields: [
      {
        name: 'ValuationDate',
        value: '09/02/2025 14:30:22'
      },
      {
        name: 'PortfolioCode',
        value: 'TECH'
      },
      {
        name: 'LusidInstrumentId',
        value: 'LUID_00004K9H'
      },
      {
        name: 'Error',
        value: "Missing market data for Quote dependency. Failed to resolve pricing data for instrument."
      },
      {
        name: 'Name',
        value: 'COMMONWEALTH BANK OF AUSTRALIA'
      },
      {
        name: 'InstrumentType',
        value: 'Equity'
      },
      {
        name: 'DomCcy',
        value: 'AUD'
      },
      {
        name: 'Ticker',
        value: 'CBA'
      },
      {
        name: 'RIC',
        value: 'CBA.AX'
      },
      {
        name: 'ISIN',
        value: 'AU000000CBA7'
      }
    ],
    actionLogIdCreated: '123bb58f-95b0-46ec-a834-3af2a2506a28'
  },

  // Child Task 3
  {
    id: '5678c6c2-a96a-4c4b-a283-549cb7b56998',
    taskDefinitionId: {
      scope: 'IBOR-DQ-ProdTeam',
      code: 'IBOR-DQ-Child-Aggregation-Error-Check'
    },
    taskDefinitionVersion: {
      asAtModified: '2025-07-24T04:42:09.9825630+00:00'
    },
    taskDefinitionDisplayName: 'Aggregation Errors Exception',
    state: 'Resolved',
    ultimateParentTask: {
      id: '2b888027-60e4-405e-82c6-bc0be9493e2e',
      taskDefinitionId: {
        scope: 'IBOR-DQ-ProdTeam',
        code: 'IBOR-DQ-Parent-Aggregation-Errors'
      },
      taskDefinitionVersion: {
        asAtModified: '2025-07-24T04:42:11.1130120+00:00'
      },
      taskDefinitionDisplayName: 'Aggregation Errors Parent Task',
      state: 'inReview'
    },
    parentTask: {
      id: '2b888027-60e4-405e-82c6-bc0be9493e2e',
      taskDefinitionId: {
        scope: 'IBOR-DQ-ProdTeam',
        code: 'IBOR-DQ-Parent-Aggregation-Errors'
      },
      taskDefinitionVersion: {
        asAtModified: '2025-07-24T04:42:11.1130120+00:00'
      },
      taskDefinitionDisplayName: 'Aggregation Errors Parent Task',
      state: 'inReview'
    },
    childTasks: [],
    correlationIds: ['Early Morning DQ'],
    version: {
      asAtCreated: '2025-08-30T09:15:45.7890123+00:00',
      userIdCreated: '00u12u680zegmCPd62p8',
      requestIdCreated: 'requestId',
      asAtModified: '2025-09-01T16:22:33.4567890+00:00',
      userIdModified: '00u12u680zegmCPd62p8',
      requestIdModified: 'requestId',
      asAtVersionNumber: 2
    },
    terminalState: true,
    asAtLastTransition: '2025-09-01T16:22:33.4567890+00:00',
    fields: [
      {
        name: 'ValuationDate',
        value: '08/30/2025 09:15:45'
      },
      {
        name: 'PortfolioCode',
        value: 'INFRA'
      },
      {
        name: 'LusidInstrumentId',
        value: 'LUID_00005L0I'
      },
      {
        name: 'Name',
        value: 'TELSTRA CORPORATION LIMITED'
      },
      {
        name: 'InstrumentType',
        value: 'Equity'
      },
      {
        name: 'DomCcy',
        value: 'AUD'
      },
      {
        name: 'Ticker',
        value: 'TLS'
      },
      {
        name: 'RIC',
        value: 'TLS.AX'
      },
      {
        name: 'ISIN',
        value: 'AU000000TLS2'
      }
    ],
    actionLogIdCreated: '567bb58f-95b0-46ec-a834-3af2a2506a28',
    actionLogIdModified: '567bb58f-95b0-46ec-a834-3af2a2506a28'
  },

  // Ultimate Parent Task 2 - Completed with no children
  {
    id: 'ac6f4add-24d9-430b-9e3a-c02e0b370a00',
    taskDefinitionId: {
      scope: 'IBOR-DQ-ProdTeam',
      code: 'IBOR-DQ-Parent-Aggregation-Errors'
    },
    taskDefinitionVersion: {
      asAtModified: '2025-07-24T04:42:11.1130120+00:00'
    },
    taskDefinitionDisplayName: 'Aggregation Errors Parent Task',
    state: 'Completed',
    childTasks: [],
    correlationIds: ['Late Morning DQ'],
    version: {
      asAtCreated: '2025-08-29T17:02:03.1790910+00:00',
      userIdCreated: '00u13czryilVQwCBO2p8',
      requestIdCreated: 'requestId',
      asAtModified: '2025-08-29T17:02:21.4754390+00:00',
      userIdModified: '00u13czryilVQwCBO2p8',
      requestIdModified: 'requestId',
      asAtVersionNumber: 2
    },
    terminalState: true,
    asAtLastTransition: '2025-08-29T17:02:21.4754390+00:00',
    fields: [],
    actionLogIdModified: 'deb6ad92-f6b6-46dc-aa7f-92bfd73e110d',
    actionLogIdSubmitted: 'deb6ad92-f6b6-46dc-aa7f-92bfd73e110d'
  }
]

// Helper function to group tasks by ultimate parent
export function groupTasksByUltimateParent(tasks: WorkflowTask[]): TaskGroup[] {
  const groups = new Map<string, TaskGroup>()

  // First pass: identify ultimate parents
  tasks.forEach(task => {
    if (!task.ultimateParentTask || task.id === task.ultimateParentTask.id) {
      // This is an ultimate parent
      if (!groups.has(task.id)) {
        groups.set(task.id, {
          ultimateParent: task,
          children: [],
          totalCount: 1
        })
      }
    }
  })

  // Second pass: assign children to their ultimate parents
  tasks.forEach(task => {
    if (task.ultimateParentTask && task.id !== task.ultimateParentTask.id) {
      const parentGroup = groups.get(task.ultimateParentTask.id)
      if (parentGroup) {
        parentGroup.children.push(task)
        parentGroup.totalCount = parentGroup.children.length + 1
      }
    }
  })

  return Array.from(groups.values()).sort((a, b) => 
    new Date(b.ultimateParent.version.asAtCreated).getTime() - 
    new Date(a.ultimateParent.version.asAtCreated).getTime()
  )
}

// Mock API response
export const mockTaskListResponse: TaskListResponse = {
  values: mockTasks,
  href: 'https://simpleflow.lusid.com/workflow/api/tasks/',
  links: [
    {
      relation: 'RequestLogs',
      href: 'https://simpleflow.lusid.com/app/insights/logs/mock-request-id',
      description: 'A link to the LUSID Insights website showing all logs related to this request',
      method: 'GET'
    }
  ]
}

// Helper to get mock task groups
export function getMockTaskGroups(): TaskGroup[] {
  return groupTasksByUltimateParent(mockTasks)
}
