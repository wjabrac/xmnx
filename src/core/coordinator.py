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

# All tools from both sides of the merge
from src.core.tools.editor import EditFileTool, LintTool
from src.core.tools.browser import BrowserTool

class TaskState(BaseModel):
    id: str
    goal: str
    status: str = "pending"  # pending, active, completed, failed
    plan: List[str] = []
    current_step_index: int = 0
    context_summary: str = ""

class Coordinator:
    """The CWD (Coordinator-Worker-Delegator) Orchestrator."""

    def __init__(self, llm: LLMProvider, brain: BrainManager, sandbox: Sandbox):
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

        # Include both Edit/Lint and Browser
        self.registry.register(EditFileTool(self.sandbox))
        self.registry.register(LintTool(self.sandbox))
        self.registry.register(BrowserTool())

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

        # 1. Build Context using PromptBuilder
        from src.core.prompts import PromptBuilder
        
        # Initialize builder (ToDo: Cache this or move to __init__)
        builder = PromptBuilder(self.registry.get_schemas())
        
        history = stream.get_history()
        messages = builder.build_messages(state.goal, self.sandbox.work_dir, history)
        
        # 2. Call LLM with Tools
        try:
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
