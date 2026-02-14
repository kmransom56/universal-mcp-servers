"""
Progress Tracker - Enables Claude Code-style autonomous execution
Tracks progress across multi-hour sessions without losing context
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import json


@dataclass
class TaskStep:
    """Individual step in a task plan"""
    id: str
    description: str
    status: str  # pending, in_progress, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    output: Optional[Dict[str, Any]] = None


@dataclass
class TaskPlan:
    """Complete task plan with checkpoint capability"""
    task_id: str
    title: str
    steps: List[TaskStep]
    created_at: str
    updated_at: str
    total_steps: int
    completed_steps: int
    current_step_index: int
    metadata: Dict[str, Any]


class ProgressTracker:
    """
    Tracks long-running task progress with checkpointing
    Enables resumption after interruption or message limit
    """
    
    def __init__(self, state_dir: Optional[Path] = None):
        if state_dir is None:
            # Try environment variable first, then user home, then local dir
            import os
            mcp_path = os.environ.get('MCP_MEMORY_PATH')
            if mcp_path:
                state_dir = Path(mcp_path) / "progress"
            else:
                # Use user home directory
                home = Path.home()
                state_dir = home / ".claude-memory" / "progress"
        
        self.state_dir = Path(state_dir)
        
        # Create directory, but handle permission errors gracefully
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            # Fall back to local directory if can't create in home
            print(f"Warning: Cannot create {state_dir}, using local directory. Error: {e}")
            self.state_dir = Path("./mcp_progress")
            self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def create_plan(
        self,
        task_id: str,
        title: str,
        steps: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        """Create new task plan"""
        
        now = datetime.now().isoformat()
        
        task_steps = [
            TaskStep(
                id=f"{task_id}_step_{i}",
                description=desc,
                status="pending"
            )
            for i, desc in enumerate(steps)
        ]
        
        plan = TaskPlan(
            task_id=task_id,
            title=title,
            steps=task_steps,
            created_at=now,
            updated_at=now,
            total_steps=len(task_steps),
            completed_steps=0,
            current_step_index=0,
            metadata=metadata or {}
        )
        
        self._save_plan(plan)
        return plan
    
    def load_plan(self, task_id: str) -> Optional[TaskPlan]:
        """Load existing task plan"""
        plan_file = self.state_dir / f"{task_id}.json"
        
        if not plan_file.exists():
            return None
        
        with open(plan_file, 'r') as f:
            data = json.load(f)
        
        # Reconstruct TaskStep objects
        data['steps'] = [TaskStep(**step) for step in data['steps']]
        
        return TaskPlan(**data)
    
    def update_step(
        self,
        task_id: str,
        step_index: int,
        status: str,
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> TaskPlan:
        """Update status of a specific step"""
        
        plan = self.load_plan(task_id)
        if not plan:
            raise ValueError(f"Task {task_id} not found")
        
        step = plan.steps[step_index]
        now = datetime.now().isoformat()
        
        # Update step
        if status == "in_progress" and step.status == "pending":
            step.started_at = now
        elif status == "completed":
            step.completed_at = now
            plan.completed_steps += 1
        elif status == "failed":
            step.completed_at = now
            step.error = error
        
        step.status = status
        if output:
            step.output = output
        
        # Update plan
        plan.updated_at = now
        if status == "in_progress":
            plan.current_step_index = step_index
        
        self._save_plan(plan)
        return plan
    
    def get_next_step(self, task_id: str) -> Optional[TaskStep]:
        """Get next pending step"""
        plan = self.load_plan(task_id)
        if not plan:
            return None
        
        for step in plan.steps:
            if step.status == "pending":
                return step
        
        return None
    
    def get_progress_summary(self, task_id: str) -> Dict[str, Any]:
        """Get human-readable progress summary"""
        plan = self.load_plan(task_id)
        if not plan:
            return {"error": "Task not found"}
        
        return {
            "task_id": task_id,
            "title": plan.title,
            "progress": f"{plan.completed_steps}/{plan.total_steps}",
            "percentage": round((plan.completed_steps / plan.total_steps) * 100, 1),
            "current_step": plan.steps[plan.current_step_index].description if plan.current_step_index < len(plan.steps) else "Complete",
            "status": "complete" if plan.completed_steps == plan.total_steps else "in_progress",
            "steps": [
                {
                    "description": step.description,
                    "status": step.status
                }
                for step in plan.steps
            ]
        }
    
    def checkpoint(self, task_id: str, checkpoint_data: Dict[str, Any]):
        """Save checkpoint data for recovery"""
        plan = self.load_plan(task_id)
        if not plan:
            raise ValueError(f"Task {task_id} not found")
        
        plan.metadata['last_checkpoint'] = {
            'timestamp': datetime.now().isoformat(),
            'data': checkpoint_data
        }
        
        self._save_plan(plan)
    
    def restore_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Restore from last checkpoint"""
        plan = self.load_plan(task_id)
        if not plan:
            return None
        
        return plan.metadata.get('last_checkpoint', {}).get('data')
    
    def _save_plan(self, plan: TaskPlan):
        """Save plan to disk"""
        plan_file = self.state_dir / f"{plan.task_id}.json"
        
        # Convert to dict for JSON serialization
        plan_dict = asdict(plan)
        
        with open(plan_file, 'w') as f:
            json.dump(plan_dict, f, indent=2)


# Example usage functions

def start_migration_task() -> TaskPlan:
    """Example: Start a FastAPI migration task"""
    tracker = ProgressTracker()
    
    return tracker.create_plan(
        task_id="fastapi_migration_phase2",
        title="FastAPI Migration Phase 2 - VLAN Endpoints",
        steps=[
            "Analyze existing Flask VLAN routes",
            "Create Pydantic schemas for VLAN operations",
            "Implement FastAPI VLAN list endpoint",
            "Implement FastAPI VLAN create endpoint",
            "Implement FastAPI VLAN update endpoint",
            "Implement FastAPI VLAN delete endpoint",
            "Add async database operations",
            "Write unit tests for VLAN endpoints",
            "Integration testing",
            "Update API documentation"
        ],
        metadata={
            "project": "network-device-mcp-server",
            "phase": 2,
            "priority": "high"
        }
    )


def resume_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Resume interrupted task"""
    tracker = ProgressTracker()
    plan = tracker.load_plan(task_id)
    
    if not plan:
        return None
    
    next_step = tracker.get_next_step(task_id)
    checkpoint = tracker.restore_checkpoint(task_id)
    
    return {
        "plan": plan,
        "next_step": next_step,
        "checkpoint_data": checkpoint,
        "summary": tracker.get_progress_summary(task_id)
    }
