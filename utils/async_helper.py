"""
Async utilities for handling concurrent operations and timeouts.
"""
import asyncio
from functools import wraps
import time


def with_timeout(timeout_sec):
    """Decorator to apply timeout to an async function."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_sec)
            except asyncio.TimeoutError:
                # Return a partial result or default value on timeout
                # This way we can still provide a response even if it's not complete
                if hasattr(func, 'timeout_fallback'):
                    return await func.timeout_fallback(*args, **kwargs)
                return {"status": "timeout", "message": f"Operation timed out after {timeout_sec} seconds."}
        return wrapper
    return decorator


def timed_execution(func):
    """Decorator to measure execution time of a function."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Attach execution time to the result if it's a dict
        if isinstance(result, dict):
            result['execution_time'] = execution_time
        
        return result
    return wrapper


async def run_tasks_with_priority(tasks_dict, timeout=None):
    """
    Run multiple tasks with priority handling.
    
    Args:
        tasks_dict: Dictionary of {task_name: (priority, coroutine)}
        timeout: Overall timeout for all tasks
    
    Returns:
        Dictionary of {task_name: result}
    """
    # Sort tasks by priority (lower number means higher priority)
    sorted_tasks = sorted(tasks_dict.items(), key=lambda x: x[1][0])
    
    results = {}
    pending = []
    
    start_time = time.time()
    remaining_time = timeout
    
    # Start all tasks
    for task_name, (priority, coro) in sorted_tasks:
        if timeout is not None:
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time <= 0:
                break
        
        task = asyncio.create_task(coro)
        task.task_name = task_name
        pending.append(task)
    
    # Wait for tasks to complete with priority handling
    while pending and (timeout is None or (time.time() - start_time) < timeout):
        done, pending = await asyncio.wait(
            pending, 
            timeout=0.1,  # Short timeout to regularly check priorities
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Process completed tasks
        for task in done:
            try:
                results[task.task_name] = task.result()
            except Exception as e:
                results[task.task_name] = {"status": "error", "message": str(e)}
    
    # Cancel any remaining tasks
    for task in pending:
        task.cancel()
        try:
            results[task.task_name] = {"status": "cancelled", "message": "Task was cancelled due to timeout."}
        except:
            pass
    
    return results


class ProgressTracker:
    """Track progress of a multi-step operation with callback notification."""
    
    def __init__(self, total_steps, callback=None):
        """
        Initialize progress tracker.
        
        Args:
            total_steps: Total number of steps
            callback: Function to call when progress updates
        """
        self.total_steps = total_steps
        self.completed_steps = 0
        self.callback = callback
        self.start_time = time.time()
        self.step_times = []
        self.status = "in_progress"
        self.partial_results = {}
    
    def update(self, step_name, result=None):
        """Update progress by one step."""
        self.completed_steps += 1
        current_time = time.time()
        step_time = current_time - self.start_time
        self.step_times.append((step_name, step_time))
        
        if result is not None:
            self.partial_results[step_name] = result
        
        if self.callback:
            self.callback(self.completed_steps, self.total_steps, step_name, result)
        
        if self.completed_steps >= self.total_steps:
            self.status = "completed"
        
        return self.get_progress()
    
    def get_progress(self):
        """Get current progress status."""
        return {
            "status": self.status,
            "progress": self.completed_steps / self.total_steps,
            "completed_steps": self.completed_steps,
            "total_steps": self.total_steps,
            "elapsed_time": time.time() - self.start_time,
            "step_times": self.step_times,
            "partial_results": self.partial_results
        } 