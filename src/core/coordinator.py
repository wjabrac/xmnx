import uuid
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from src.core.events.stream import EventStream
from src.core.events.types import Event, ActionEvent, ObservationEvent
from src.memory.fs.manager import BrainManager
from src.runtime.sandbox.interface import Sandbox
from src.interfaces.llm import LLMProvider
from src.core.registry import ToolRegistry
from src.core.tools.shell import ShellTool
from src.core.tools.filesystem import ReadFileTool, WriteFileTool, ListFilesTool

class TaskState(BaseModel):
    id: str
    goal: str
    status: str = "pending" # pending, active, completed, failed
    plan: List[str] = []
    current_step_index: int = 0
    context_summary: str = ""

class Coordinator:
    """
    The CWD (Coordinator-Worker-Delegator) Orchestrator.
    Manages the high-level lifecycle of a Task.
    """
    def __init__(self, 
                 llm: LLMProvider, 
                 brain: BrainManager, 
                 sandbox: Sandbox):
        self.llm = llm
        self.brain = brain
        self.sandbox = sandbox
        self.active_tasks: Dict[str, TaskState] = {}
        
        # Initialize Tool Registry
        self.registry = ToolRegistry()
        self._register_default_tools()

    def _register_default_tools(self):
        self.registry.register(ShellTool(self.sandbox))
        self.registry.register(ReadFileTool(self.sandbox))
        self.registry.register(WriteFileTool(self.sandbox))
        self.registry.register(ListFilesTool(self.sandbox))

    def start_task(self, goal: str) -> str:
        """
        Initialize a new task, set up its brain, and generate an initial plan.
        """
        task_id = str(uuid.uuid4())
        
        # 1. Initialize Memory
        stream = self.brain.get_stream(task_id)
        stream.publish(Event(
            source="user",
            type="control",
            task_id=task_id,
            content={"action": "start_task", "goal": goal}
        ))

        # 2. Create State
        state = TaskState(id=task_id, goal=goal)
        self.active_tasks[task_id] = state
        state.status = "active"
        
        return task_id

    def tick(self, task_id: str):
        """
        Execute one step of the Coordinator loop.
        """
        if task_id not in self.active_tasks:
            return

        state = self.active_tasks[task_id]
        stream = self.brain.get_stream(task_id)

        # 1. Build Context
        history = stream.get_history()
        messages = self._build_prompt(state, history)
        
        # 2. Call LLM with Tools
        try:
            # We assume the LLMProvider handles the raw API call.
            # Ideally we'd pass `tools=self.registry.get_schemas()` here.
            # But LiteLLMProvider.completion interface needs to support it.
            # For now, we'll patch specific params in the call directly.
            
            # Using LiteLLM's provider directly for now to ensure tool passing works
            from litellm import completion
            response = completion(
                model=self.llm.model,
                messages=messages,
                tools=self.registry.get_schemas(),
                tool_choice="auto",
                api_key=self.llm.api_key
            )
            
            msg = response.choices[0].message
            content = msg.content or ""
            tool_calls = msg.tool_calls

            # Log Thought
            if content:
                stream.publish(Event(
                    source="coordinator",
                    type="thought",
                    task_id=task_id,
                    content={"thought": content}
                ))

            # 3. Execute Tools
            if tool_calls:
                for tc in tool_calls:
                    func_name = tc.function.name
                    args_str = tc.function.arguments
                    try:
                        args = json.loads(args_str)
                    except:
                        args = {}

                    # Log Action
                    stream.publish(ActionEvent(
                        source="coordinator",
                        task_id=task_id,
                        tool=func_name,
                        args=args,
                        content={"action": "call_tool", "tool": func_name}
                    ))

                    # Execute
                    tool = self.registry.get_tool(func_name)
                    if tool:
                        result = tool.run(**args)
                    else:
                        result = {"error": f"Tool {func_name} not found"}

                    # Log Observation
                    stream.publish(ObservationEvent(
                        source="sandbox",
                        task_id=task_id,
                        output=str(result),
                        content={"observation": result}
                    ))

        except Exception as e:
            stream.publish(ObservationEvent(
                source="system",
                task_id=task_id,
                output=str(e),
                error=str(e),
                content={"error": str(e)}
            ))

    def _build_prompt(self, state: TaskState, history: List[Event]) -> List[Dict]:
        """Construct the prompt from event history."""
        system_prompt = f"""You are XMNX, an autonomous agent.
Goal: {state.goal}
Working Directory: {self.sandbox.work_dir}

Instructions:
1. Analyze the history.
2. Formulate a plan if needed.
3. Use tools to execute the plan step by step.
4. Verify your work.
"""
        messages = [{"role": "system", "content": system_prompt}]
        
        for event in history:
            if event.type == "thought":
                messages.append({"role": "assistant", "content": event.content.get("thought", "")})
            elif event.type == "action":
                # In a real replay, we'd need to reconstruct the tool_calls structure
                # For simplicity, we just append a user message summarizing the action execution
                pass 
            elif event.type == "observation":
                messages.append({"role": "user", "content": f"Observation: {event.content}"})
            elif event.type == "control" and event.source == "user":
                 messages.append({"role": "user", "content": f"Request: {event.content.get('goal', '')}"})

        return messages
