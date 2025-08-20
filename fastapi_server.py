#!/usr/bin/env python3
"""
FastAPI server for Universal Email Agent
Provides REST API endpoints for email automation
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
import asyncio
import logging
from datetime import datetime
import uuid
from email_agent import UniversalEmailAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Universal Email Agent API",
    description="Cross-platform email automation service",
    version="1.0.0"
)

# Request/Response Models
class EmailRequest(BaseModel):
    instruction: str = Field(..., description="Natural language email instruction")
    providers: List[str] = Field(default=["gmail"], description="Email providers to use")
    headless: bool = Field(default=True, description="Run browser in headless mode")
    
    class Config:
        schema_extra = {
            "example": {
                "instruction": "Send an email to john@example.com about project update saying 'Phase 1 completed'",
                "providers": ["gmail", "outlook"],
                "headless": True
            }
        }

class EmailResponse(BaseModel):
    task_id: str
    status: str
    results: Dict[str, bool]
    message: str
    timestamp: datetime

class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    results: Optional[Dict[str, bool]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

# In-memory task storage (in production, use Redis or database)
tasks: Dict[str, TaskStatus] = {}

class EmailTaskRunner:
    """Async wrapper for email agent tasks"""
    
    @staticmethod
    async def run_email_task(task_id: str, instruction: str, providers: List[str], headless: bool = True):
        """Run email task asynchronously"""
        try:
            # Update task status
            tasks[task_id].status = "running"
            logger.info(f"Starting email task {task_id}")
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            agent = UniversalEmailAgent(headless=headless)
            
            # Execute the task
            results = await loop.run_in_executor(
                None, 
                agent.execute_email_task, 
                instruction, 
                providers
            )
            
            # Update task with results
            tasks[task_id].status = "completed"
            tasks[task_id].results = results
            tasks[task_id].completed_at = datetime.now()
            
            logger.info(f"Completed email task {task_id}: {results}")
            
        except Exception as e:
            logger.error(f"Email task {task_id} failed: {str(e)}")
            tasks[task_id].status = "failed"
            tasks[task_id].error = str(e)
            tasks[task_id].completed_at = datetime.now()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Universal Email Agent API",
        "status": "active",
        "timestamp": datetime.now()
    }

@app.post("/email/send", response_model=EmailResponse)
async def send_email(request: EmailRequest, background_tasks: BackgroundTasks):
    """
    Send email via specified providers
    Returns immediately with task ID for async processing
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Validate providers
        supported_providers = ["gmail", "outlook"]
        invalid_providers = [p for p in request.providers if p.lower() not in supported_providers]
        if invalid_providers:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported providers: {invalid_providers}. Supported: {supported_providers}"
            )
        
        # Create task
        task = TaskStatus(
            task_id=task_id,
            status="pending",
            created_at=datetime.now()
        )
        tasks[task_id] = task
        
        # Start background task
        background_tasks.add_task(
            EmailTaskRunner.run_email_task,
            task_id,
            request.instruction,
            request.providers,
            request.headless
        )
        
        return EmailResponse(
            task_id=task_id,
            status="pending",
            results={},
            message="Email task queued successfully",
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue email task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/email/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get status of email task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return tasks[task_id]

@app.get("/email/tasks")
async def list_tasks():
    """List all email tasks"""
    return {
        "tasks": list(tasks.values()),
        "total": len(tasks)
    }

@app.delete("/email/tasks")
async def clear_tasks():
    """Clear all completed tasks"""
    completed_count = sum(1 for task in tasks.values() if task.status in ["completed", "failed"])
    tasks.clear()
    return {"message": f"Cleared {completed_count} tasks"}

@app.post("/email/analyze")
async def analyze_provider(provider: str):
    """Analyze DOM structure of a provider"""
    try:
        if provider.lower() not in ["gmail", "outlook"]:
            raise HTTPException(status_code=400, detail="Unsupported provider")
        
        agent = UniversalEmailAgent(headless=True)
        loop = asyncio.get_event_loop()
        
        analysis = await loop.run_in_executor(
            None, 
            agent.analyze_dom_structure, 
            provider
        )
        
        return {
            "provider": provider,
            "analysis": analysis,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"DOM analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/providers")
async def list_providers():
    """List supported email providers"""
    return {
        "providers": [
            {
                "name": "gmail",
                "display_name": "Gmail Web",
                "url": "https://mail.google.com",
                "supported": True
            },
            {
                "name": "outlook", 
                "display_name": "Outlook Web",
                "url": "https://outlook.live.com",
                "supported": True
            }
        ]
    }

# WebSocket endpoint for real-time task updates (optional)
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/task/{task_id}")
async def websocket_task_updates(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task status updates"""
    await websocket.accept()
    
    try:
        while True:
            if task_id in tasks:
                task = tasks[task_id]
                await websocket.send_json({
                    "task_id": task_id,
                    "status": task.status,
                    "results": task.results,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Close connection when task completes
                if task.status in ["completed", "failed"]:
                    break
            
            await asyncio.sleep(1)  # Poll every second
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task {task_id}")

if __name__ == "__main__":
    # CLI interface
    import sys
    
    if len(sys.argv) > 1:
        # Command line mode
        instruction = " ".join(sys.argv[1:])
        
        async def cli_main():
            agent = UniversalEmailAgent(headless=False)
            results = agent.execute_email_task(instruction, ["gmail"])
            print(f"Results: {results}")
        
        asyncio.run(cli_main())
    else:
        # Server mode
        print("Starting Universal Email Agent API server...")
        print("API documentation available at: http://localhost:8000/docs")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")