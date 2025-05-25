"""Main entry point for the browser agent application."""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Optional

from src.agent.browser_agent_v1 import BrowserAgent
from src.agent.task_executor import TaskExecutor
from src.tasks.web_tasks import (
    WebScrapingTask,
    FormFillingTask,
    NavigationTask,
    DataExtractionTask
)
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.helpers import load_from_json, save_to_json


async def run_single_task(task_type: str, **kwargs) -> None:
    """Run a single task."""
    async with BrowserAgent() as agent:
        task = None
        
        if task_type == "scrape":
            task = WebScrapingTask(
                task_id="scrape-1",
                url=kwargs.get("url"),
                selectors=kwargs.get("selectors", {}),
                wait_for_selector=kwargs.get("wait_selector")
            )
        
        elif task_type == "fill_form":
            task = FormFillingTask(
                task_id="form-1",
                url=kwargs.get("url"),
                form_data=kwargs.get("form_data", {}),
                submit_selector=kwargs.get("submit_selector")
            )
        
        elif task_type == "navigate":
            task = NavigationTask(
                task_id="nav-1",
                urls=kwargs.get("urls", []),
                actions=kwargs.get("actions", [])
            )
        
        elif task_type == "extract":
            task = DataExtractionTask(
                task_id="extract-1",
                url=kwargs.get("url"),
                extraction_prompt=kwargs.get("prompt", ""),
                output_format=kwargs.get("format", "json")
            )
        
        if task:
            result = await agent.execute(task)
            logger.info(f"Task completed: {result.status.value}")
            
            if result.data:
                output_file = kwargs.get("output", "output.json")
                save_to_json(result.to_dict(), output_file)
                logger.info(f"Results saved to {output_file}")


async def run_task_executor(tasks_file: str) -> None:
    """Run multiple tasks using task executor."""
    # Load tasks from file
    tasks_data = load_from_json(tasks_file)
    
    # Create executor
    executor = TaskExecutor(
        max_concurrent_tasks=settings.agent_max_steps,
        max_agents=3
    )
    
    await executor.initialize()
    
    # Create tasks
    tasks = []
    for task_data in tasks_data:
        task_type = task_data.get("type")
        
        if task_type == "scrape":
            task = WebScrapingTask(**task_data)
        elif task_type == "fill_form":
            task = FormFillingTask(**task_data)
        elif task_type == "navigate":
            task = NavigationTask(**task_data)
        elif task_type == "extract":
            task = DataExtractionTask(**task_data)
        else:
            logger.warning(f"Unknown task type: {task_type}")
            continue
        
        tasks.append(task)
    
    # Add tasks to executor
    await executor.add_tasks(tasks)
    
    # Run executor
    executor_task = asyncio.create_task(executor.run())
    
    # Wait for all tasks to complete
    while await executor.task_queue.size() > 0 or executor.active_tasks:
        await asyncio.sleep(1)
        status = executor.get_status()
        logger.info(
            f"Active: {status['active_tasks']}, "
            f"Completed: {status['completed_tasks']}, "
            f"Queued: {status['queue_size']}"
        )
    
    # Stop executor
    await executor.stop()
    executor_task.cancel()
    
    # Save results
    results = executor.get_task_results()
    output_file = "results.json"
    save_to_json([r.__dict__ for r in results], output_file)
    logger.info(f"All tasks completed. Results saved to {output_file}")


async def interactive_mode() -> None:
    """Run in interactive mode."""
    async with BrowserAgent() as agent:
        logger.info("Interactive mode started. Type 'exit / quit / q' to quit.")
        
        while True:
            try:
                task_description = input("\nEnter task description: ")
                
                if task_description.lower() in ['exit', 'quit', 'q']:
                    option = input("\nDo you really want to quit from the interactive mode? [Yes(y)/No(n)]")
                    if option.lower() in ('y', 'yes'):
                        print("Exiting the interactive mode")
                        break
                    print("Starting the interactive mode")
                    continue

                max_steps = int(input("\n Enter maximum number of steps the AI Agent Can do: "))
                if max_steps > 500:
                    print("Provide less number of steps, initiating again......")
                    continue
                if not task_description:
                    continue
                
                result = await agent.execute(task_description, max_steps)
                
                if result.success:
                    logger.info(f"Task completed successfully!")
                    if result.data:
                        print(f"Result: {result.data}")
                else:
                    logger.error(f"Task failed: {result.error}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error: {str(e)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Browser Agent - AI-powered web automation"
    )
    
    parser.add_argument(
        "mode",
        choices=["single", "batch", "interactive"],
        help="Execution mode"
    )
    
    # Single task arguments
    parser.add_argument(
        "--task",
        choices=["scrape", "fill_form", "navigate", "extract"],
        help="Task type for single mode"
    )
    parser.add_argument("--url", help="Target URL")
    parser.add_argument("--selectors", help="JSON file with CSS selectors")
    parser.add_argument("--wait-selector", help="Selector to wait for")
    parser.add_argument("--form-data", help="JSON file with form data")
    parser.add_argument("--submit-selector", help="Submit button selector")
    parser.add_argument("--urls", nargs="+", help="List of URLs for navigation")
    parser.add_argument("--actions", help="JSON file with navigation actions")
    parser.add_argument("--prompt", help="Extraction prompt")
    parser.add_argument("--format", default="json", help="Output format")
    parser.add_argument("--output", default="output.json", help="Output file")
    
    # Batch mode arguments
    parser.add_argument("--tasks-file", help="JSON file with task definitions")
    
    # General arguments
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Update settings based on arguments
    if args.headless:
        settings.browser_headless = True
    if args.debug:
        settings.log_level = "DEBUG"
    
    # Run appropriate mode
    try:
        if args.mode == "single":
            if not args.task or not args.url:
                parser.error("Single mode requires --task and --url arguments")
            
            kwargs = {
                "url": args.url,
                "output": args.output
            }
            
            if args.task == "scrape":
                if args.selectors:
                    kwargs["selectors"] = load_from_json(args.selectors)
                else:
                    parser.error("Scrape task requires --selectors argument")
                kwargs["wait_selector"] = args.wait_selector
            
            elif args.task == "fill_form":
                if args.form_data:
                    kwargs["form_data"] = load_from_json(args.form_data)
                else:
                    parser.error("Form fill task requires --form-data argument")
                kwargs["submit_selector"] = args.submit_selector
            
            elif args.task == "navigate":
                kwargs["urls"] = args.urls or [args.url]
                if args.actions:
                    kwargs["actions"] = load_from_json(args.actions)
            
            elif args.task == "extract":
                if not args.prompt:
                    parser.error("Extract task requires --prompt argument")
                kwargs["prompt"] = args.prompt
                kwargs["format"] = args.format
            
            asyncio.run(run_single_task(args.task, **kwargs))
        
        elif args.mode == "batch":
            if not args.tasks_file:
                parser.error("Batch mode requires --tasks-file argument")
            
            asyncio.run(run_task_executor(args.tasks_file))
        
        elif args.mode == "interactive":
            asyncio.run(interactive_mode())
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()