# Fathom Implementation Plan

**Project**: LUSID Data-Quality Agent with Agno Agent UI  
**Created**: January 2025  
**Status**: Development Phase

## Overview

Building Fathom as a specialized LUSID workflow task investigation tool using the existing Agno Agent UI framework. The implementation will replace the current chat blank state with a dynamic task panel that allows users to filter, select, and investigate LUSID workflow tasks.

## Current State Analysis

**What We Have:**
- ✅ Agno Agent UI fully set up with all dependencies
- ✅ LUSID credentials configured (secrets.json in root)
- ✅ LUSID API endpoints accessible at https://simpleflow.lusid.com/api
- ✅ Shadcn UI MCP server configured for UI components
- ✅ Modern React/Next.js stack with TypeScript

**What We Need:**
- Task panel component replacing ChatBlankState
- Backend Fathom agent with LUSID API integration
- Azure storage setup for audit/sessions (later phase)
- Model gateway configuration (later phase)

## Implementation Strategy

**Order of Implementation:**
1. **UI Foundation** - Task panel with mock data
2. **Backend Setup** - Agno Playground with Fathom agent
3. **LUSID Integration** - Real API data and tools
4. **Model Gateway** - Azure OpenAI/Claude integration
5. **Storage & Audit** - Azure persistence layer

## Phase 1: Task Panel UI Foundation (Week 1)

### 1.1 Mock Data Structure
Create LUSID-aligned mock data that matches real API responses:

```typescript
interface WorkflowTask {
  id: string
  taskDefinitionDisplayName: string
  state: 'Open' | 'InProgress' | 'Completed' | 'Failed'
  asAtLastTransition: string // ISO date
  ultimateParent?: {
    id: string
    name: string
  }
  children?: WorkflowTask[]
  fields: Array<{
    name: string
    value: any
    displayName?: string
  }>
  // Portfolio context
  portfolioScope?: string
  portfolioCode?: string
  valuationDate?: string
  // Instrument context
  instrumentIdType?: string
  instrumentIdValue?: string
}
```

### 1.2 Task Panel Component
Replace `ChatBlankState` with new `TaskPanel` component:

**Location**: `agent-ui/src/components/playground/ChatArea/TaskPanel/`
- `TaskPanel.tsx` - Main container
- `TaskList.tsx` - Hierarchical task list
- `TaskItem.tsx` - Individual expandable task row
- `DateFilter.tsx` - Calendar dropdown filter
- `TaskChips.tsx` - Selected task chips in composer

**Key Features:**
- Date filter dropdown (filters by `asAtLastTransition`)
- Hierarchical expandable rows (Ultimate Parent → Task → Children)
- Task selection adds chips to composer
- Search functionality across task names and states
- Responsive design matching current UI aesthetic

### 1.3 State Management
Extend existing Zustand store:

```typescript
interface TaskStore {
  // Task panel state
  selectedTasks: WorkflowTask[]
  taskFilter: {
    dateFrom?: string
    dateTo?: string
    searchQuery?: string
    states?: string[]
  }
  // Actions
  addSelectedTask: (task: WorkflowTask) => void
  removeSelectedTask: (taskId: string) => void
  setTaskFilter: (filter: Partial<TaskStore['taskFilter']>) => void
  clearSelectedTasks: () => void
}
```

### 1.4 Integration Points
- Modify `Messages.tsx` to show TaskPanel when `messages.length === 0`
- Update ChatInput to handle task chips
- Ensure task selection disappears when user starts chatting

**Deliverables:**
- Task panel replaces blank state
- Mock data displays realistic LUSID tasks
- Date filtering works
- Task selection/deselection with chips
- Smooth transition to chat mode

## Phase 2: Backend Foundation (Week 2)

### 2.1 Project Structure
Create backend in new directory:
```
fathom/
├── agent-ui/           # Existing UI
├── backend/            # New FastAPI backend
│   ├── fathom/
│   │   ├── agent.py    # Fathom agent definition
│   │   ├── tools/      # LUSID tools
│   │   ├── clients/    # LUSID API clients
│   │   └── config/     # Configuration files
│   ├── playground.py   # Agno Playground setup
│   ├── requirements.txt
│   └── .env.example
├── docs/
└── secrets.json       # Existing LUSID credentials
```

### 2.2 Agno Playground Setup
Install and configure Agno Playground:

```python
# playground.py
from agno.playground import Playground
from fathom.agent import build_fathom_agent

agent = build_fathom_agent(
    name="Fathom",
    model_alias="gpt-4o-mini",  # Start with basic model
    tools=[]  # Empty initially
)

playground = Playground(agents=[agent])
app = playground.get_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7777)
```

### 2.3 LUSID API Clients
Create API clients using existing credentials:

```python
# fathom/clients/lusid_client.py
from lusid.utilities import ApiClientFactory
from lusidjam import RefreshingToken
import os

class LUSIDClient:
    def __init__(self):
        self.api_factory = ApiClientFactory(
            token=RefreshingToken(),
            api_secrets_filename="secrets.json",  # Root level
            app_name="Fathom"
        )
        self.access_token = self.api_factory.api_client.configuration.access_token
        
    def get_workflow_tasks(self, date_filter=None, state_filter=None):
        # GET /workflow/api/tasks
        pass
        
    def get_task_details(self, task_id):
        # GET /workflow/api/tasks/{id}
        pass
```

### 2.4 Fathom Endpoints
Add custom endpoints for task management:

```python
# Custom endpoints in playground
@app.get("/fathom/tasks")
async def get_tasks(date: str = None, state: str = None):
    # Return hierarchical task list
    pass

@app.post("/fathom/investigate")
async def investigate_tasks(request: InvestigateRequest):
    # Handle task investigation
    pass
```

**Deliverables:**
- Agno Playground running on localhost:7777
- LUSID API client authenticated and working
- Basic Fathom agent registered
- Custom endpoints returning mock data
- UI successfully connects to backend

## Phase 3: LUSID Integration (Week 3)

### 3.1 Workflow API Integration
Implement real LUSID Workflow API calls:

```python
# fathom/tools/workflow_tools.py
class WorkflowGetTask:
    def __init__(self, client):
        self.client = client
        
    async def run(self, task_id: str):
        """Get full task details"""
        return await self.client.get_task_details(task_id)

class WorkflowListTasks:
    async def run(self, date_from=None, date_to=None, state=None):
        """List tasks with filters"""
        pass
```

### 3.2 Honeycomb SQL Tools
Implement Luminesce SQL tools for data investigation:

```python
# fathom/tools/sql_tools.py
class GetSysFields:
    async def run(self, table_names: List[str]):
        """Get system fields for validation"""
        sql = """
        SELECT TableName, FieldName, DataType, FieldType, IsPrimaryKey, Description 
        FROM Sys.Field 
        WHERE TableName IN @table_names 
        ORDER BY TableName, FieldName
        """
        return await self.execute_sql(sql, {"table_names": table_names})

class GetInstrument:
    async def run(self, identifiers: List[str]):
        """Resolve instrument details"""
        pass
```

### 3.3 Task Field Mapping
Create configuration for mapping task fields to semantic meaning:

```yaml
# fathom/config/task_field_map.yaml
field_mappings:
  portfolio_scope:
    - "PortfolioScope"
    - "Scope"
  portfolio_code:
    - "PortfolioCode" 
    - "Code"
  valuation_date:
    - "ValuationDate"
    - "AsAt"
  instrument_id:
    - "LusidInstrumentId"
    - "InstrumentId"
```

### 3.4 Evidence Gathering
Implement investigation orchestration:

```python
# fathom/agent.py
async def investigate_tasks(task_ids: List[str], question: str):
    # 1. Fetch full task details
    tasks = [await wf_get_task(tid) for tid in task_ids]
    
    # 2. Extract context from task fields
    context = normalize_tasks(tasks, task_field_map)
    
    # 3. Run investigation tools
    evidence = await gather_evidence(context)
    
    # 4. Return structured findings
    return {
        "summary": "...",
        "suspected_error_type": "...", 
        "evidence": evidence,
        "next_steps": "..."
    }
```

**Deliverables:**
- Real LUSID task data in UI
- Working SQL tools for data investigation
- Task field mapping and context extraction
- Basic investigation workflow
- Error handling for API failures

## Phase 4: Model Gateway & Reasoning (Week 4)

### 4.1 Azure OpenAI Setup
Configure Azure OpenAI integration:

```python
# fathom/config/models.yaml
models:
  claude-azure:
    provider: "azure_anthropic"
    model: "claude-3-5-sonnet-20241022"
    temperature: 0.2
    max_tokens: 4096
    
  gpt-4o-azure:
    provider: "azure_openai"
    model: "gpt-4o"
    temperature: 0.2
    max_tokens: 4096
```

### 4.2 Investigation Reasoning
Implement structured reasoning with models:

```python
# fathom/reasoning/investigator.py
class TaskInvestigator:
    def __init__(self, model_gateway):
        self.model_gateway = model_gateway
        
    async def analyze_tasks(self, tasks, evidence):
        prompt = self.build_investigation_prompt(tasks, evidence)
        
        response = await self.model_gateway.generate(
            prompt=prompt,
            response_format="json",
            schema=InvestigationResultSchema
        )
        
        return self.format_markdown_response(response)
```

### 4.3 Response Formatting
Structure agent responses with consistent markdown format:

```markdown
## Investigation Summary
Brief 1-3 line summary of findings.

## Suspected Error Type
- **Type**: Data Quality Issue / Missing Price / Stale Holdings
- **Confidence**: High/Medium/Low

## Evidence
### Query Results
- **Query ID**: ABC123
- **Rows Found**: 15
- **Sample Data**: [truncated table]

## Suggested Next Steps
1. Check instrument pricing for ISIN XYZ
2. Verify portfolio holdings as of date
3. Review transaction history

## Technical Details
- **Model**: claude-azure
- **Run ID**: def456
- **Duration**: 2.3s
```

**Deliverables:**
- Azure OpenAI configured and working
- Structured investigation reasoning
- Consistent markdown response format
- Model switching capability
- Error type classification

## Phase 5: Storage & Audit (Week 5)

### 5.1 Azure Storage Setup
Configure Azure Table Storage and Blob Storage:

```python
# fathom/storage/azure_storage.py
class AzureSessionStore:
    def __init__(self, connection_string):
        self.table_client = TableClient.from_connection_string(
            connection_string, "FathomSessions"
        )
        
class AzureAuditSink:
    def __init__(self, connection_string):
        self.table_client = TableClient.from_connection_string(
            connection_string, "FathomAudit"
        )
```

### 5.2 Audit Schema
Implement comprehensive audit logging:

```json
{
  "run_id": "uuid",
  "event_type": "run|tool_call|model_io|error",
  "task_id": "string",
  "portfolio_scope": "string",
  "portfolio_code": "string", 
  "model_alias": "string",
  "query_id": "string",
  "row_count": "number",
  "duration_ms": "number",
  "confidence": "number",
  "created_at": "iso_date"
}
```

### 5.3 Session Management
Integrate with Agno's session system:

```python
# Update agent registration
agent = build_fathom_agent(
    model_alias="claude-azure",
    session_store=AzureSessionStore(connection_string),
    audit_sink=AzureAuditSink(connection_string)
)
```

**Deliverables:**
- Azure storage configured
- Session persistence working
- Comprehensive audit logging
- Performance metrics tracking
- Data retention policies

## Phase 6: Polish & Production Readiness (Week 6)

### 6.1 Error Handling & UX
- Loading states for all operations
- Graceful error handling with user-friendly messages
- Retry logic for transient failures
- Progress indicators for long-running operations

### 6.2 Performance Optimization
- Caching for frequently accessed tasks
- Pagination for large task lists
- Background refresh of task data
- Query optimization for SQL tools

### 6.3 Documentation & Deployment
- Setup documentation (README.md)
- Environment configuration (.env.example)
- API documentation
- Deployment scripts

### 6.4 Testing & Validation
- End-to-end testing with real LUSID data
- Model response validation
- Performance benchmarking
- Security review

**Deliverables:**
- Production-ready application
- Complete documentation
- Deployment automation
- Performance monitoring
- Security hardening

## Technical Decisions & Rationale

**Project Structure**: Keeping UI in `agent-ui/` subdirectory maintains compatibility with Agno ecosystem while allowing backend to be separate.

**Mock-First Approach**: Building UI with realistic mock data ensures we can iterate quickly on UX without API dependencies.

**Gradual Integration**: Phased approach allows us to validate each component before adding complexity.

**Azure Later**: Deferring storage setup until core functionality works reduces initial complexity and setup overhead.

## Success Criteria

**MVP Acceptance**:
- ✅ Task list displays with hierarchy and date filtering
- ✅ Task selection adds chips to composer
- ✅ "Investigate" triggers end-to-end analysis
- ✅ Returns markdown findings with evidence
- ✅ Audit entries recorded in Azure
- ✅ Model alias displayed in responses

**Performance Targets**:
- Task list loads < 2 seconds
- Investigation completes < 30 seconds
- UI remains responsive during operations

**Quality Gates**:
- No TypeScript errors
- All components properly tested
- LUSID API errors handled gracefully
- Audit data complete and accurate

## Next Steps

1. **Start with Phase 1** - TaskPanel component with mock data
2. **Validate UX flow** - Ensure task selection → chat transition works smoothly  
3. **Set up backend** - Get Agno Playground running with basic Fathom agent
4. **Iterate rapidly** - Get feedback on each phase before proceeding

This implementation plan balances rapid progress with solid foundations, allowing us to demonstrate value quickly while building toward a production-ready system.
