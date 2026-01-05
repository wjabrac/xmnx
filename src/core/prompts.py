from typing import List, Dict, Any, Optional
from src.core.events.types import Event

class PromptBuilder:
    """
    Constructs the System Prompt and Message History for the LLM.
    Responsibility:
    - Inject Agent Persona & Constraints
    - Format Tool schemas (if not handled natively)
    - Inject Context/Memory
    - Format History (Events -> Messages)
    """

    BASE_SYSTEM_PROMPT = """You are XMNX, an advanced autonomous AI agent.
Your purpose is to achieve the user's Goal efficiently and safely.

## OPERATIONAL CONSTRAINTS
1. **Safety First**: Never execute destructive commands without verification.
2. **Hermetic**: You are running in a restricted sandbox. You cannot access the internet unless via a specific tool.
3. **Persistence**: Your state is saved. You can stop and resume.

## TOOL USAGE
- You have access to a set of tools.
- You MUST use the provided tools to interact with the world.
- Do NOT hallucinate capabilities you do not have.

## DECISION LOOP
1. **OBSERVE**: Look at the history and current state.
2. **REFLECT**: specific errors or past failures?
3. **PLAN**: What is the next immediate step?
4. **ACT**: Execute the tool.
"""

    def __init__(self, tools_schemas: List[Dict[str, Any]]):
        self.tools_schemas = tools_schemas

    def build_system_message(self, goal: str, work_dir: str) -> str:
        """
        Dynamically assembles the system prompt.
        """
        prompt = self.BASE_SYSTEM_PROMPT
        prompt += f"\n## CURRENT CONTEXT\n"
        prompt += f"**GOAL**: {goal}\n"
        prompt += f"**WORKING DIR**: {work_dir}\n"
        
        # NOTE: If we were using an LLM without native tool calling, 
        # we would inject tool schemas here.
        
        return prompt

    def build_messages(self, 
                      goal: str, 
                      work_dir: str, 
                      history: List[Event], 
                      max_tokens: int = 4000) -> List[Dict[str, str]]:
        """
        Converts internal Event stream into LLM-compatible messages.
        """
        system_msg = self.build_system_message(goal, work_dir)
        messages = [{"role": "system", "content": system_msg}]
        
        # Optimization: We could implement token counting/truncation here
        # For now, we just append all history
        
        for event in history:
            if event.type == "thought":
                content = event.content.get("thought")
                if content:
                    messages.append({"role": "assistant", "content": content})
            
            elif event.type == "action":
                # Actions are implicit in tool calls usually, but for history re-injection:
                tool_name = event.content.get("tool")
                if tool_name:
                    # In a formal chat API, this might need to be a tool_use message
                    # For simple prompting, we can narrate it or skip if using native tool history
                    pass 

            elif event.type == "observation":
                content = event.content.get("observation")
                # Native tool APIs usually require a tool_result message matching a tool_use_id
                # Since our Event structure flattens this, we approximate for now:
                messages.append({"role": "user", "content": f"Tool Output: {content}"})

            elif event.type == "control" and event.source == "user":
                 request = event.content.get("goal")
                 if request:
                     messages.append({"role": "user", "content": f"New Request: {request}"})

        return messages
