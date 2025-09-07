from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from fathom.models.tasks import WorkflowTask, TaskFilter
import lusid
import os

router = APIRouter()

# We'll initialize the LUSID client per request to avoid async issues


def group_tasks_by_ultimate_parent(tasks: List[WorkflowTask]) -> List[dict]:
    """Group tasks by ultimate parent, matching frontend TaskGroup structure"""
    groups = {}
    
    # First pass: identify ultimate parents
    for task in tasks:
        if not task.ultimateParentTask or task.id == task.ultimateParentTask.id:
            # This is an ultimate parent
            if task.id not in groups:
                groups[task.id] = {
                    "ultimateParent": task,
                    "children": [],
                    "totalCount": 1
                }
    
    # Second pass: assign children to their ultimate parents
    for task in tasks:
        if task.ultimateParentTask and task.id != task.ultimateParentTask.id:
            parent_id = task.ultimateParentTask.id
            if parent_id in groups:
                groups[parent_id]["children"].append(task)
                groups[parent_id]["totalCount"] = len(groups[parent_id]["children"]) + 1
    
    # Sort by creation date (newest first)
    return sorted(
        groups.values(), 
        key=lambda g: g["ultimateParent"].version.asAtCreated, 
        reverse=True
    )


def create_lusid_client(app) -> "LUSIDClient":
    """Create a LUSID client using the shared ApiClientFactory from app.state"""
    from fathom.clients.lusid_client import LUSIDClient
    factory: lusid.ApiClientFactory | None = getattr(app.state, "lusid_factory", None)
    secrets_path = os.path.abspath(os.getenv("FBN_SECRETS_PATH") or os.getenv("LUSID_SECRETS_PATH") or os.path.join(os.path.dirname(__file__), "..", "..", "..", "secrets.json"))
    return LUSIDClient(factory, secrets_path)

@router.get("/tasks")
async def get_tasks(
    dateFrom: Optional[str] = Query(None, description="Filter tasks from this date (YYYY-MM-DD)"),
    dateTo: Optional[str] = Query(None, description="Filter tasks to this date (YYYY-MM-DD)"),
    searchQuery: Optional[str] = Query(None, description="Search across task names and fields"),
    states: Optional[str] = Query(None, description="Comma-separated list of states to filter by"),
    correlationIds: Optional[str] = Query(None, description="Comma-separated list of correlation IDs to filter by")
):
    """Fetch and filter LUSID workflow tasks"""
    try:
        # Create LUSID client per request (uses shared factory)
        # FastAPI passes request via dependency or we can reach app via router routes; simplest is to use
        # the global app reference by importing from main
        from main import app
        lusid_client = create_lusid_client(app)
        
        # Parse query parameters
        task_filter = TaskFilter(
            dateFrom=dateFrom,
            dateTo=dateTo,
            searchQuery=searchQuery,
            states=states.split(",") if states else None,
            correlationIds=correlationIds.split(",") if correlationIds else None
        )
        
        # Fetch tasks from LUSID
        response = await lusid_client.get_workflow_tasks(task_filter)
        tasks = response.values
        
        # Apply client-side filtering for unsupported LUSID filters
        filtered_tasks = lusid_client.filter_tasks_locally(tasks, task_filter)
        
        # Group tasks by ultimate parent (matching frontend structure)
        grouped_tasks = group_tasks_by_ultimate_parent(filtered_tasks)
        
        return {
            "taskGroups": grouped_tasks,
            "totalTasks": len(filtered_tasks),
            "totalGroups": len(grouped_tasks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Fetch detailed information for a specific task"""
    try:
        from main import app
        lusid_client = create_lusid_client(app)
        task = await lusid_client.get_task_details(task_id)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task: {str(e)}")
