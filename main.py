import os
import argparse
import sys
import time
from dotenv import load_dotenv

from src.core.events.stream import EventStream
from src.memory.fs.manager import BrainManager
from src.memory.vector.engine import VectorEngine
from src.runtime.sandbox.local import LocalSandbox
from src.runtime.browser.engine import HermeticBrowser
from src.interfaces.litellm import LiteLLMProvider
from src.core.coordinator import Coordinator

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="XMNX: The Ultimate Agent Runtime")
    parser.add_argument("--goal", type=str, required=True, help="The goal for the agent to achieve")
    parser.add_argument("--steps", type=int, default=10, help="Max steps to run")
    args = parser.parse_args()

    print("🚀 Initializing XMNX...")

    # 1. Initialize Components
    # Brain
    brain = BrainManager(base_path="z:/home/willux/Others/XMNX/brain")
    
    # Runtime (Sandbox + Browser)
    sandbox = LocalSandbox(work_dir="z:/home/willux/Others/XMNX/workspace")
    # browser = HermeticBrowser() # Keep disabled for now until needed

    # LLM
    llm = LiteLLMProvider(model="gpt-4o") # Default to OpenAI for now
    
    # Coordinator
    coordinator = Coordinator(llm, brain, sandbox)

    # 2. Start Task
    print(f"🎯 Goal: {args.goal}")
    task_id = coordinator.start_task(args.goal)
    print(f"✅ Task Started! ID: {task_id}")

    # 3. Main Loop
    step = 0
    while step < args.steps:
        print(f"🔄 Step {step+1}/{args.steps}...")
        coordinator.tick(task_id)
        
        # Check status (naive check for now)
        # In real impl, checking coordinator.active_tasks[task_id].status
        
        step += 1
        time.sleep(1) # Polite delay

    print("🏁 Max steps reached. Exiting.")

if __name__ == "__main__":
    main()
