import os
import requests
from typing import List, Optional, Dict, Any
import lusid
from lusid.extensions.configuration_loaders import SecretsFileConfigurationLoader
from fathom.models.tasks import WorkflowTask, TaskListResponse, TaskFilter


class LUSIDClient:
    def __init__(self, api_factory: lusid.ApiClientFactory, secrets_path: str):
        """Initialize LUSID client with an already-initialised ApiClientFactory"""
        self.workflow_base_url = "https://simpleflow.lusid.com/workflow/api"
        self._api_factory = api_factory
        self.secrets_path = os.path.abspath(secrets_path)

    def _get_access_token(self) -> str:
        """Get or refresh access token from the factory configuration"""
        if self._api_factory is None:
            raise RuntimeError("LUSID ApiClientFactory not initialised")

        # Build a lightweight API to hydrate api_client
        api = self._api_factory.build(lusid.ApplicationMetadataApi)
        cfg = api.api_client.configuration
        token = getattr(cfg, "access_token", None)
        if not token:
            # Try to force a call to hydrate token (versions may vary)
            try:
                _ = api.get_lusid_versions()
                token = getattr(api.api_client.configuration, "access_token", None)
            except Exception:
                token = getattr(api.api_client.configuration, "access_token", None)
        if not token:
            raise RuntimeError("Empty LUSID access token")
        return str(token)
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make authenticated request to LUSID API"""
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.workflow_base_url}{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_workflow_tasks(self, task_filter: Optional[TaskFilter] = None) -> TaskListResponse:
        """Fetch workflow tasks from LUSID. We avoid server-side filters for stability and filter locally."""
        params: Dict[str, Any] = {}
        try:
            data = self._make_request("/tasks", params)
            return TaskListResponse(**data)
        except Exception as e:
            raise Exception(f"Failed to fetch LUSID tasks: {str(e)}")
    
    async def get_task_details(self, task_id: str) -> WorkflowTask:
        """Fetch detailed information for a specific task"""
        try:
            data = self._make_request(f"/tasks/{task_id}")
            return WorkflowTask(**data)
        except Exception as e:
            raise Exception(f"Failed to fetch task {task_id}: {str(e)}")
    
    def filter_tasks_locally(self, tasks: List[WorkflowTask], task_filter: TaskFilter) -> List[WorkflowTask]:
        """Apply client-side filtering for fields not supported by LUSID API"""
        filtered_tasks = tasks
        
        # Search filtering
        if task_filter.searchQuery:
            query = task_filter.searchQuery.lower()
            filtered_tasks = [
                task for task in filtered_tasks
                if (query in task.taskDefinitionDisplayName.lower() or 
                    query in task.state.lower() or
                    any(query in field.name.lower() or 
                        (field.value and query in str(field.value).lower()) 
                        for field in task.fields))
            ]
        
        # Correlation ID filtering (batch filtering)
        if task_filter.correlationIds:
            filtered_tasks = [
                task for task in filtered_tasks
                if any(corr_id in task.correlationIds for corr_id in task_filter.correlationIds)
            ]
        
        return filtered_tasks
