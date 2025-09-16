"""
Dynamic agent loader for executing agents on demand.
Handles loading, instantiation, and execution of dynamic agents.
"""

import asyncio
import importlib.util
import inspect
import logging
import sys
import tempfile
from typing import Dict, Any, Optional, Callable, Awaitable
from pathlib import Path
from datetime import datetime

from .agent_cache import AgentCache
from .backend_client import BackendClient
# from ...core.assistant_compiler import (
#     AssistantCompiler, 
#     AssistantDefinition, 
#     ModelConfig, 
#     VoiceConfig, 
#     TranscriberConfig, 
#     ToolConfig, 
#     AnalysisConfig, 
#     SpeakingPlanConfig
#     )
from ...core.workflow_compiler import WorkflowCompiler

logger = logging.getLogger(__name__)


class DynamicAgentLoader:
    """Loader for dynamic agent execution"""

    def __init__(self, cache: AgentCache, backend_client: BackendClient):
        self.cache = cache
        self.backend_client = backend_client
        self.temp_dir = Path(tempfile.mkdtemp(prefix="dynamic_agents_"))

        # Initialize compilers
        # self.assistant_compiler = AssistantCompiler()
        self.workflow_compiler = WorkflowCompiler()

    def load_or_save_agent_definition(self, tenant_id: str, agent_definition: Dict[str, Any]) -> None:
        pass

    async def get_agent_instance(
        self,
        type_: str,
        tenant_id: str,
        agent_id: str,
        job_context: Any,
        agent_definition: Dict[str, Any]
    ) -> Any:
        """
        Load and execute an agent dynamically using existing compilers.

        Args:
            tenant_id: Organization/Tenant identifier
            agent_id: Agent identifier
            job_context: LiveKit job context
            agent_definition: Agent configuration from backend

        Returns:
            Agent execution result
        """
        cache_key = f"{tenant_id}:{agent_id}"

        try:
            # Check if agent is cached
            cached_module = self.cache.get_cached_module(cache_key)

            if cached_module:
                logger.info(f"Using cached agent: {cache_key}")
                # Determine agent type for cached modules
                cached_agent_type = "workflow" if self._is_workflow_definition(agent_definition) else "assistant"
                # return await self._execute_agent(cached_module, job_context, cached_agent_type, agent_definition)

            # Determine agent type and use appropriate compiler
            if type_ == "workflow":
                logger.info(f"Compiling workflow agent: {cache_key}")
                agent_code = self.workflow_compiler.compile_from_dict(agent_definition)
            else:
                logger.info(f"Compiling assistant agent: {cache_key}")
                # Convert backend format to compiler format
                assistant_def = self._convert_to_assistant_definition(agent_definition)
                agent_code = self.assistant_compiler.compile_assistant(assistant_def)

            # Load the agent module
            module = await self._load_agent_module(cache_key, agent_code, agent_definition, type_)

            # Cache the module for future use
            definition_hash = self._calculate_definition_hash(agent_definition)
            self.cache.cache_module(cache_key, module, definition_hash)

            # Execute the agent
            # print(module)
            # await module.entrypoint(job_context)
            # return await self._execute_agent(module, job_context, agent_type, agent_definition)
            return module.initialize_agent()

        except Exception as e:
            logger.error(f"Error loading/executing agent {cache_key}: {e}")
            raise

    async def _load_agent_module(
        self, 
        cache_key: str, 
        agent_code: str,
        agent_definition: Dict[str, Any], 
        agent_type: str
        ) -> Any:
        """Load agent code as a Python module"""
        try:
            # Create temporary file for the agent code
            temp_file = self.temp_dir / f"{cache_key.replace(':', '_')}.py"
            temp_file = rf"C:\Users\Engr Ogundeko\Desktop\SolveByte\boboyii\app\agent_runtime\examples\example_workflow.py"


            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(agent_code)

            logger.info(f"Created agent file: {temp_file}")

            # Load the module using importlib
            spec = importlib.util.spec_from_file_location(
                f"dynamic_agent_{cache_key.replace(':', '_')}",
                temp_file
            )

            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load agent module: {cache_key}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            logger.info(f"Successfully loaded agent module: {cache_key}")
            return module

        except Exception as e:
            logger.error(f"Failed to load agent module {cache_key}: {e}")
            raise



    # async def _get_entrypoint(
    #         self, 
    #         module: Any
    #         ) -> Any:
    #     """Execute the loaded agent module"""
    #     re

    def _calculate_definition_hash(self, definition: Dict[str, Any]) -> str:
        """Calculate hash of agent definition for caching"""
        import hashlib
        definition_str = str(sorted(definition.items()))
        return hashlib.sha256(definition_str.encode()).hexdigest()

    def _is_workflow_definition(self, json_data: Dict[str, Any]) -> bool:
        """Determine if JSON data represents a workflow or assistant definition"""
        # Workflow definitions have nodes and edges
        return "nodes" in json_data and "edges" in json_data

    def _convert_to_assistant_definition(self, backend_definition: Dict[str, Any]) -> AssistantDefinition:
        """Convert backend assistant definition to compiler format"""
        try:
            # Extract configuration from backend format
            model_provider = backend_definition.get("model_provider", "openai")
            model = backend_definition.get("model", "gpt-4o")
            temperature = backend_definition.get("temperature", 0.7)
            max_tokens = backend_definition.get("max_tokens", 250)

            voice_provider = backend_definition.get("voice_provider", "deepgram")
            voice = backend_definition.get("voice", "aura-asteria-en")

            transcriber_provider = backend_definition.get("transcriber_provider", "deepgram")
            transcriber_model = backend_definition.get("transcriber_model", "nova-2")
            language = backend_definition.get("language", "en")

            # Create compiler-compatible objects
            model_config = ModelConfig(
                provider=model_provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            voice_config = VoiceConfig(
                provider=voice_provider,
                voice=voice
            )

            transcriber_config = TranscriberConfig(
                provider=transcriber_provider,
                model=transcriber_model,
                language=language
            )

            # Convert tools if present
            tools = {}
            if backend_definition.get("tools"):
                for tool_name in backend_definition["tools"]:
                    tools[tool_name] = ToolConfig(name=tool_name, enabled=True)

            # Create analysis config
            analysis_config = AnalysisConfig(
                summary_enabled=backend_definition.get("analysis_summary", True),
                structured_data_enabled=backend_definition.get("analysis_structured_data", False)
            )

            # Create speaking plan config
            speaking_plan_config = SpeakingPlanConfig(
                enabled=True,  # Always enable speaking plan
                response_delay=0.5
            )

            return AssistantDefinition(
                name=backend_definition.get("name", "Dynamic Assistant"),
                template=backend_definition.get("template", "Blank Template"),
                prompt=backend_definition.get("prompt", "You are a helpful assistant."),
                model=model_config,
                voice=voice_config,
                transcriber=transcriber_config,
                tools=tools,
                analysis=analysis_config,
                speaking_plan=speaking_plan_config,
                global_variables=backend_definition.get("global_variables")
            )

        except Exception as e:
            logger.error(f"Error converting backend definition: {e}")
            # Return a basic fallback definition
            return AssistantDefinition(
                name="Fallback Assistant",
                template="Blank Template",
                prompt="You are a helpful assistant.",
                model=ModelConfig(),
                voice=VoiceConfig(),
                transcriber=TranscriberConfig(),
                tools={},
                analysis=AnalysisConfig(),
                speaking_plan=SpeakingPlanConfig()
            )

    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up temporary agent files")
        except Exception as e:
            logger.warning(f"Error cleaning up temp files: {e}")

    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup_temp_files()
