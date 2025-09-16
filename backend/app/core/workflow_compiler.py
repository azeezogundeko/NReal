#!/usr/bin/env python3
"""
LiveKit Workflow Compiler (Updated)

Converts JSON workflow definitions into Python LiveKit agent code.
Supports dynamic configuration of LLM, TTS, and STT providers.
"""

import json
import re
import textwrap
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from pathlib import Path


class PythonJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts Python values to proper Python syntax"""

    def encode(self, obj):
        """Override encode to convert Python values to proper syntax"""
        if isinstance(obj, dict):
            return "{" + ", ".join(f'{repr(k)}: {self._encode_value(v)}' for k, v in obj.items()) + "}"
        elif isinstance(obj, list):
            return "[" + ", ".join(self._encode_value(item) for item in obj) + "]"
        else:
            return self._encode_value(obj)

    def _encode_value(self, value):
        """Encode a single value with proper Python syntax"""
        if value is None:
            return "None"
        elif value is True:
            return "True"
        elif value is False:
            return "False"
        elif isinstance(value, str):
            return repr(value)
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, dict):
            return self.encode(value)
        elif isinstance(value, list):
            return "[" + ", ".join(self._encode_value(item) for item in value) + "]"
        else:
            return repr(value)


@dataclass
class WorkflowNode:
    """Represents a workflow node"""
    name: str
    type: str
    prompt: Optional[str] = None
    variable_extraction_plan: Optional[Dict] = None
    message_plan: Optional[Dict] = None
    global_node_plan: Optional[Dict] = None
    tool: Optional[Dict] = None
    metadata: Optional[Dict] = None
    is_start: bool = False
    # AI Provider Settings
    llm_config: Optional[Dict] = None
    voice_config: Optional[Dict] = None
    transcriber_config: Optional[Dict] = None


@dataclass
class WorkflowEdge:
    """Represents a workflow edge/transition"""
    from_node: str
    to_node: str
    condition: Dict[str, Any]


@dataclass
class WorkflowDefinition:
    """Complete workflow definition"""
    name: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    global_prompt: str = ""
    global_llm_config: Optional[Dict] = None
    global_voice_config: Optional[Dict] = None
    global_transcriber_config: Optional[Dict] = None
    global_variables: Optional[Dict] = None


class WorkflowParser:
    """Parses JSON workflow into structured data"""

    def parse(self, json_data: Dict[str, Any]) -> WorkflowDefinition:
        """Parse JSON workflow into WorkflowDefinition"""
        nodes = []
        for node_data in json_data.get("nodes", []):
            metadata = node_data.get("metadata", {})
            node = WorkflowNode(
                name=node_data["name"],
                type=node_data["type"],
                prompt=node_data.get("prompt"),
                variable_extraction_plan=node_data.get("variableExtractionPlan"),
                message_plan=node_data.get("messagePlan"),
                global_node_plan=node_data.get("globalNodePlan"),
                tool=node_data.get("tool"),
                metadata=metadata,
                is_start=node_data.get("isStart", False),
                llm_config=metadata.get("llmConfig") or node_data.get("llmConfig"),
                voice_config=metadata.get("voiceConfig") or node_data.get("voiceConfig"),
                transcriber_config=metadata.get("transcriberConfig") or node_data.get("transcriberConfig")
            )
            nodes.append(node)

        edges = []
        for edge_data in json_data.get("edges", []):
            edge = WorkflowEdge(
                from_node=edge_data["from"],
                to_node=edge_data["to"],
                condition=edge_data["condition"]
            )
            edges.append(edge)

        return WorkflowDefinition(
            name=json_data.get("name", "Workflow Agent"),
            nodes=nodes,
            edges=edges,
            global_prompt=json_data.get("globalPrompt", ""),
            global_llm_config=json_data.get("globalLlmConfig"),
            global_voice_config=json_data.get("globalVoiceConfig"),
            global_transcriber_config=json_data.get("globalTranscriberConfig"),
            global_variables=json_data.get("globalVariables")
        )


class WorkflowValidator:
    """Validates workflow structure and dependencies"""

    def validate(self, workflow: WorkflowDefinition) -> List[str]:
        """Validate workflow and return list of errors"""
        errors = []
        start_nodes = [n for n in workflow.nodes if n.is_start]
        if len(start_nodes) == 0:
            errors.append("No start node found. One node must have 'isStart': True")
        elif len(start_nodes) > 1:
            errors.append(f"Multiple start nodes found: {[n.name for n in start_nodes]}")

        node_names = [n.name for n in workflow.nodes]
        if len(node_names) != len(set(node_names)):
            errors.append("Node names must be unique")

        for edge in workflow.edges:
            if edge.from_node not in node_names:
                errors.append(f"Edge references non-existent node: {edge.from_node}")
            if edge.to_node not in node_names:
                errors.append(f"Edge references non-existent node: {edge.to_node}")

        reachable = set()
        if start_nodes:
            self._mark_reachable(start_nodes[0].name, workflow.edges, reachable)

        global_nodes = [n.name for n in workflow.nodes if n.global_node_plan and n.global_node_plan.get("enabled")]
        reachable.update(global_nodes)
        tool_nodes = [n.name for n in workflow.nodes if n.type == "tool"]
        reachable.update(tool_nodes)

        unreachable = set(node_names) - reachable
        if unreachable:
            unreachable_conversation = [n for n in unreachable if any(node.name == n and node.type == "conversation" for node in workflow.nodes)]
            if unreachable_conversation:
                errors.append(f"Unreachable conversation nodes found: {unreachable_conversation}")

        return errors

    def _mark_reachable(self, node_name: str, edges: List[WorkflowEdge], reachable: Set[str]):
        """Recursively mark reachable nodes"""
        if node_name in reachable:
            return
        reachable.add(node_name)
        for edge in edges:
            if edge.from_node == node_name:
                self._mark_reachable(edge.to_node, edges, reachable)


class PythonCodeGenerator:
    """Generates Python LiveKit agent code from workflow"""

    def __init__(self):
        self.variable_registry = set()
        self.node_functions = []
        self.transition_functions = []

    def generate(self, workflow: WorkflowDefinition) -> str:
        """Generate complete Python agent code"""
        self._extract_variables(workflow)
        imports = self._generate_imports()
        state_class = self._generate_state_class()
        utilities = self._generate_utilities()
        node_handlers = self._generate_node_handlers(workflow)
        main_agent = self._generate_main_agent(workflow)
        entry_point = self._generate_entry_point(workflow)

        return f"""# Auto-generated Boboyii Workflow Agent
# Generated from: {workflow.name}

{imports}

{state_class}

{utilities}

{node_handlers}

{main_agent}

{entry_point}
"""

    def _extract_variables(self, workflow: WorkflowDefinition):
        """Extract all variable names from the workflow"""
        for node in workflow.nodes:
            if node.variable_extraction_plan:
                outputs = node.variable_extraction_plan.get("output", [])
                for output in outputs:
                    self.variable_registry.add(output.get("title", ""))
            if node.prompt:
                template_vars = re.findall(r'\{\{(\w+)\}\}', node.prompt)
                self.variable_registry.update(template_vars)

    def _generate_imports(self) -> str:
        """Generate import statements"""
        return textwrap.dedent("""
        import asyncio
        import json
        import logging
        import re
        from typing import Dict, Any, Optional, List, Union, Tuple
        from dataclasses import dataclass, field

        import aiohttp
        from livekit import agents
        from livekit.agents import (
            Agent,
            cli,
            AgentSession,
            WorkerOptions,
            JobContext,
            function_tool
        )
        from livekit.agents.llm import (
            ChatContext,
            ChatMessage
        )
        from dotenv import load_dotenv
        load_dotenv()

        # Import plugins with fallbacks for problematic dependencies
        try:
            from livekit.plugins import openai, deepgram, cartesia, silero, groq
            PLUGINS_AVAILABLE = True
        except ImportError as e:
            PLUGINS_AVAILABLE = False
            print(f"Warning: Could not import all plugins. Some providers may not be available. Error: {e}")

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        """).strip()

    def _generate_state_class(self) -> str:
        """Generate state management class"""
        variables = "\n            ".join([f"{var}: str = ''" for var in self.variable_registry if var])
        return textwrap.dedent(f"""
        @dataclass
        class WorkflowState:
            \"\"\"Manages workflow state and extracted variables\"\"\"
            current_node: str = ""
            session_id: str = ""
            {variables}
            conversation_history: List[Dict[str, str]] = field(default_factory=list)
            global_variables: Dict[str, str] = field(default_factory=dict)

            def get_variable(self, name: str) -> str:
                return self.global_variables.get(name, getattr(self, name, ""))

            def set_variable(self, name: str, value: str):
                if hasattr(self, name):
                    setattr(self, name, value)
                    logger.info(f"Set variable {{name}} = {{value}}")
                else:
                    self.global_variables[name] = value
                    logger.info(f"Set global variable {{name}} = {{value}}")

            def add_to_history(self, role: str, content: str):
                self.conversation_history.append({{
                    "role": role,
                    "content": content,
                    "timestamp": str(asyncio.get_event_loop().time())
                }})

            def format_prompt_template(self, template: str) -> str:
                import datetime
                result = template
                now = datetime.datetime.now()
                global_replacements = {{
                    "now": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M:%S"),
                }}
                global_replacements.update(self.global_variables)
                for var_name in re.findall(r'\\{{\\{{(\\w+(?:\\.\\w+)*)\\}}\\}}', template):
                    value = global_replacements.get(var_name, self.get_variable(var_name))
                    result = result.replace(f"{{{{{{var_name}}}}}}", str(value))
                return result
        """).strip()

    def _generate_utilities(self) -> str:
        """Generate utility functions"""
        return textwrap.dedent("""
        class VariableExtractor:
            \"\"\"Extracts variables from user responses using LLM\"\"\"
            def __init__(self, llm_client):
                self.llm = llm_client

            async def extract_variables(self, user_message: str, extraction_plan: Dict) -> Dict[str, str]:
                if not extraction_plan or "output" not in extraction_plan:
                    return {}
                variables_to_extract = extraction_plan["output"]
                if not variables_to_extract:
                    return {}
                var_descriptions = [f"- {var['title']}: {var['description']}" for var in variables_to_extract]
                extraction_prompt = f\"\"\"
                Extract the following variables from the user's message: "{user_message}"
                Variables to extract:
                {chr(10).join(var_descriptions)}
                Return a JSON object with variable names as keys and extracted values as strings.
                If a variable cannot be determined, use an empty string. Return only valid JSON.
                \"\"\"
                try:
                    response = await self.llm.achat(messages=[ChatMessage(role="user", content=extraction_prompt)])
                    extracted = json.loads(response.message.content)
                    valid_vars = {{var["title"]: str(extracted[var["title"]]) for var in variables_to_extract if var["title"] in extracted and extracted[var["title"]]}}
                    return valid_vars
                except Exception as e:
                    logger.warning(f"Variable extraction failed: {e}")
                    return {}

        class TransitionEvaluator:
            \"\"\"Evaluates AI-based transition conditions\"\"\"
            def __init__(self, llm_client):
                self.llm = llm_client

            async def should_transition(self, condition_prompt: str, user_message: str, conversation_history: List[Dict]) -> bool:
                context_messages = [f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:]]
                evaluation_prompt = f\"\"\"
                Based on the conversation and user's message, is the following condition met?
                CONDITION: {condition_prompt}
                CONVERSATION:
                {chr(10).join(context_messages)}
                USER'S MESSAGE: {user_message}
                Respond with exactly "TRUE" or "FALSE".
                \"\"\"
                try:
                    response = await self.llm.achat(messages=[ChatMessage(role="user", content=evaluation_prompt)])
                    return response.message.content.strip().upper() == "TRUE"
                except Exception as e:
                    logger.warning(f"Transition evaluation failed: {e}")
                    return False

        class ProviderConfigManager:
            \"\"\"Manages dynamic AI provider configurations\"\"\"
            def __init__(self, global_llm_config=None, global_voice_config=None, global_transcriber_config=None):
                self.global_llm_config = global_llm_config or {}
                self.global_voice_config = global_voice_config or {}
                self.global_transcriber_config = global_transcriber_config or {}

            def get_llm_client(self, node_llm_config=None):
                config = {**self.global_llm_config, **(node_llm_config or {})}
                provider = config.pop("provider", "openai").lower()
                logger.info(f"Configuring LLM client for provider: {provider} with config: {config}")
                try:
                    if provider == "openai": return openai.LLM(**config)
                    elif provider == "groq": return groq.LLM(**config)
                    else:
                        logger.warning(f"Unsupported LLM provider: {provider}. Falling back to OpenAI.")
                        return openai.LLM()
                except Exception as e:
                    logger.error(f"Error creating LLM client for {provider}: {e}")
                    return openai.LLM()

            def get_tts_client(self, node_voice_config=None):
                config = {**self.global_voice_config, **(node_voice_config or {})}
                provider = config.pop("provider", "deepgram").lower()
                logger.info(f"Configuring TTS client for provider: {provider} with config: {config}")
                try:
                    if provider == "openai":
                        if "voice_name" in config: config["voice"] = config.pop("voice_name")
                        return openai.TTS(**config)
                    elif provider == "deepgram":
                        if "voice_name" in config: config["model"] = config.pop("voice_name")
                        return deepgram.TTS(**config)
                    elif provider == "cartesia": return cartesia.TTS(**config)
                    else:
                        logger.warning(f"Unsupported TTS provider: {provider}. Falling back to Deepgram.")
                        return deepgram.TTS()
                except Exception as e:
                    logger.error(f"Error creating TTS client for {provider}: {e}")
                    return deepgram.TTS()

            def get_stt_client(self, node_transcriber_config=None):
                config = {**self.global_transcriber_config, **(node_transcriber_config or {})}
                provider = config.pop("provider", "deepgram").lower()
                logger.info(f"Configuring STT client for provider: {provider} with config: {config}")
                try:
                    if provider == "deepgram": return deepgram.STT(**config)
                    elif provider == "openai": return openai.STT(**config)
                    else:
                        logger.warning(f"Unsupported STT provider: {provider}. Falling back to Deepgram.")
                        return deepgram.STT()
                except Exception as e:
                    logger.error(f"Error creating STT client for {provider}: {e}")
                    return deepgram.STT()

        async def make_api_request(url: str, method: str = "POST", headers: Dict = None, data: Dict = None) -> Dict:
            headers = headers or {"Content-Type": "application/json"}
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(method.upper(), url, headers=headers, json=data) as response:
                        return {"status_code": response.status, "data": await response.json() if response.content_type == "application/json" else await response.text()}
            except Exception as e:
                logger.error(f"API request failed: {e}")
                return {"error": str(e)}
        """).strip()

    def _generate_node_handlers(self, workflow: WorkflowDefinition) -> str:
        handlers = []
        for node in workflow.nodes:
            if node.type == "conversation":
                handlers.append(self._generate_conversation_handler(node, workflow))
            elif node.type == "tool":
                handlers.append(self._generate_tool_handler(node, workflow))
        return "\n\n".join(handlers)

    def _generate_conversation_handler(self, node: WorkflowNode, workflow: WorkflowDefinition) -> str:
        func_name = self._sanitize_name(node.name)
        outgoing_edges = [e for e in workflow.edges if e.from_node == node.name]
        transition_list = [f'({repr(edge.condition.get("prompt", ""))}, "{edge.to_node}")' for edge in outgoing_edges]
        transitions_str = f"[{', '.join(transition_list)}]" if transition_list else "[]"
        
        return textwrap.dedent(f"""
        async def handle_{func_name}(state: WorkflowState, user_message: str, llm_client, variable_extractor: VariableExtractor, transition_evaluator: TransitionEvaluator, provider_config: ProviderConfigManager) -> Optional[Tuple[str, Any]]:
            \"\"\"Handle {node.name} conversation node\"\"\"
            logger.info(f"Handling {node.name} node")
            state.current_node = "{node.name}"
            state.add_to_history("user", user_message)
            
            transitions = {transitions_str}
            for edge_condition, target_node in transitions:
                if await transition_evaluator.should_transition(edge_condition, user_message, state.conversation_history):
                    state.current_node = target_node
                    logger.info(f"Transitioning from {node.name} to {{target_node}}")
                    # Return a message indicating transition, as the new node will be handled in the next turn
                    return (f"Transitioning to {{target_node}}", provider_config.get_tts_client())

            if {bool(node.variable_extraction_plan)}:
                extracted_vars = await variable_extractor.extract_variables(user_message, {json.dumps(node.variable_extraction_plan)})
                for var_name, var_value in extracted_vars.items():
                    state.set_variable(var_name, var_value)

            node_llm_config = {PythonJSONEncoder().encode(node.llm_config)}
            node_llm_client = provider_config.get_llm_client(node_llm_config)

            node_voice_config = {PythonJSONEncoder().encode(node.voice_config)}
            tts_client = provider_config.get_tts_client(node_voice_config)

            global_prompt = {repr(workflow.global_prompt or "")}
            node_prompt = {repr(node.prompt or "")}
            instruction = "\\n\\nIMPORTANT: Your reply must be very short and conversational."
            combined_prompt = f"{{global_prompt}}\\n\\n--- Node Instructions ---\\n{{node_prompt}} {{instruction}}"
            formatted_prompt = state.format_prompt_template(combined_prompt)
            
            context_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in state.conversation_history[-10:]]
            context_messages.insert(0, ChatMessage(role="system", content=formatted_prompt))
            
            try:
                response = await node_llm_client.achat(messages=context_messages)
                ai_response = response.message.content
                state.add_to_history("assistant", ai_response)
                logger.info(f"Generated response for {node.name}: {{ai_response[:100]}}...")
                return (ai_response, tts_client)
            except Exception as e:
                logger.error(f"Error in {node.name}: {{e}}")
                return ("I'm having trouble processing that right now.", tts_client)
        """).strip()

    def _generate_tool_handler(self, node: WorkflowNode, workflow: WorkflowDefinition) -> str:
        # Simplified for brevity; the original logic for different tools can be retained here.
        func_name = self._sanitize_name(node.name)
        return textwrap.dedent(f"""
        async def handle_{func_name}(state: WorkflowState) -> str:
            \"\"\"Handle {node.name} tool node\"\"\"
            logger.info(f"Executing tool node: {node.name}")
            # Add specific tool logic here (apiRequest, endCall, etc.)
            return "Tool execution completed."
        """).strip()

    def _generate_main_agent(self, workflow: WorkflowDefinition) -> str:
        start_node = next((n for n in workflow.nodes if n.is_start), workflow.nodes[0])
        agent_class = self._sanitize_class_name(workflow.name)
        
        # Create a dictionary of function references for handlers
        handler_map = {}
        for node in workflow.nodes:
            handler_map[node.name] = f"handle_{self._sanitize_name(node.name)}"

        return textwrap.dedent(f"""
        class {agent_class}(Agent):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.state = WorkflowState()
                self.variable_extractor = None
                self.transition_evaluator = None
                self.provider_config = None
                self.handler_map = {{}}

            async def start(self, session: AgentSession):
                self.state.session_id = session.id
                logger.info(f"Starting {agent_class} with session {{self.state.session_id}}")
                initial_message = await self.get_initial_message()
                if initial_message:
                    tts = self.provider_config.get_tts_client()
                    await session.say(initial_message, tts=tts)

            def set_handlers(self, handlers: Dict[str, callable]):
                self.handler_map = handlers

            async def initialize_components(self, llm_client, global_llm_config=None, global_voice_config=None, global_transcriber_config=None, global_variables=None):
                self.variable_extractor = VariableExtractor(llm_client)
                self.transition_evaluator = TransitionEvaluator(llm_client)
                self.provider_config = ProviderConfigManager(
                    global_llm_config=global_llm_config,
                    global_voice_config=global_voice_config,
                    global_transcriber_config=global_transcriber_config
                )
                if global_variables:
                    self.state.global_variables.update(global_variables)
                logger.info("Agent components initialized")

            async def process_workflow_message(self, user_message: str, llm_client) -> Tuple[Optional[str], Any]:
                if not self.state.current_node:
                    self.state.current_node = "{start_node.name}"
                
                current_node_name = self.state.current_node
                handler = self.handler_map.get(current_node_name)
                
                if not handler:
                    logger.error(f"No handler for node: {{current_node_name}}")
                    return ("I have a technical issue.", None)

                node_obj = next((n for n in workflow_nodes if n['name'] == current_node_name), None)
                if not node_obj:
                    return (f"Configuration for node {{current_node_name}} not found.", None)

                try:
                    if node_obj['type'] == 'conversation':
                        response, tts_client = await handler(
                            self.state, user_message, llm_client, self.variable_extractor, self.transition_evaluator, self.provider_config
                        )
                        # If a transition occurred, the new node will be processed on the next user input
                        return response, tts_client
                    elif node_obj['type'] == 'tool':
                        tool_response = await handler(self.state)
                        return tool_response, self.provider_config.get_tts_client() # Use default TTS for tool responses
                except Exception as e:
                    logger.error(f"Error processing message: {{e}}", exc_info=True)
                    return ("I encountered an error.", None)
                return ("No response generated.", None)

            async def get_initial_message(self) -> str:
                start_node_data = next((n for n in workflow_nodes if n.get('is_start')), None)
                if start_node_data and start_node_data.get('message_plan', {}).get('firstMessage'):
                    msg = start_node_data['message_plan']['firstMessage']
                    self.state.add_to_history("assistant", msg)
                    return msg
                return "Hello! How can I help you today?"
        """).strip()

    def _generate_entry_point(self, workflow: WorkflowDefinition) -> str:
        agent_class = self._sanitize_class_name(workflow.name)
        
        node_data_for_agent = [{
            "name": n.name, "type": n.type, "prompt": n.prompt,
            "message_plan": n.message_plan, "is_start": n.is_start,
            "voice_config": n.voice_config, "llm_config": n.llm_config
        } for n in workflow.nodes]

        return f"""
workflow_nodes = {PythonJSONEncoder().encode(node_data_for_agent)}

async def entrypoint(ctx: JobContext):
    logger.info(f"Starting {workflow.name} agent")
    
    # Initialize LLM with a default/fallback
    llm_client = openai.LLM(model="gpt-4o")

    # Initialize agent and its components
    agent = {agent_class}()
    
    global_llm_config = {PythonJSONEncoder().encode(workflow.global_llm_config) or '{{}}'}
    global_voice_config = {PythonJSONEncoder().encode(workflow.global_voice_config) or '{{}}'}
    global_transcriber_config = {PythonJSONEncoder().encode(workflow.global_transcriber_config) or '{{}}'}
    global_variables = {PythonJSONEncoder().encode(workflow.global_variables) or '{{}}'}

    await agent.initialize_components(
        llm_client,
        global_llm_config=global_llm_config,
        global_voice_config=global_voice_config,
        global_transcriber_config=global_transcriber_config,
        global_variables=global_variables
    )
    
    # Dynamically create a map of node names to handler functions
    handler_map = {{}}
    for node in workflow_nodes:
        func_name = "handle_" + re.sub(r'[^a-zA-Z0-9_]', '_', node['name']).lower()
        if func_name in globals():
            handler_map[node['name']] = globals()[func_name]
    agent.set_handlers(handler_map)

    # Configure session with global provider settings from the workflow
    stt_client = agent.provider_config.get_stt_client()
    tts_client = agent.provider_config.get_tts_client()
    vad_client = silero.VAD.load()

    session = AgentSession(
        stt=stt_client,
        llm=llm_client,  # Main LLM for core agent logic, can be overridden in nodes
        tts=tts_client,  # Default TTS, will be overridden by node-specific configs
        vad=vad_client,
        agent=agent,
    )

    @session.on("user_speech_committed")
    async def on_user_speech(ev):
        user_message = ev.user_transcript
        logger.info(f"User said: {{user_message}}")
        response_text, tts_override = await agent.process_workflow_message(user_message, llm_client)
        if response_text:
            await session.say(response_text, tts=tts_override)
            logger.info(f"Agent responded: {{response_text[:100]}}...")

    await session.start(ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
"""

    def _sanitize_name(self, name: str) -> str:
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        return f"node_{sanitized}" if sanitized and sanitized[0].isdigit() else sanitized.lower()

    def _sanitize_class_name(self, name: str) -> str:
        words = re.findall(r'[a-zA-Z0-9]+', name)
        return ''.join(word.capitalize() for word in words) + "Agent"


class WorkflowCompiler:
    """Main compiler class"""
    def __init__(self):
        self.parser = WorkflowParser()
        self.validator = WorkflowValidator()
        self.generator = PythonCodeGenerator()

    def compile_from_file(self, json_file: str, output_file: Optional[str] = None) -> str:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        return self.compile_from_dict(json_data, output_file)

    def compile_from_dict(self, json_data: Dict[str, Any], output_file: Optional[str] = None) -> str:
        workflow = self.parser.parse(json_data)
        errors = self.validator.validate(workflow)
        if errors:
            raise ValueError(f"Workflow validation failed:\\n" + "\\n".join(errors))
        
        python_code = self.generator.generate(workflow)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(python_code)
            print(f"Generated agent code written to: {output_file}")
        
        return python_code


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Compile JSON workflow to LiveKit Python agent")
    parser.add_argument("input", help="Input JSON file path")
    parser.add_argument("-o", "--output", help="Output Python file", default="workflow_agent.py")
    args = parser.parse_args()
    
    try:
        compiler = WorkflowCompiler()
        python_code = compiler.compile_from_file(args.input, args.output)
        print("Compilation successful!")
        print(f"To run with LiveKit: livekit-agents run --entrypoint-fnc entrypoint {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()