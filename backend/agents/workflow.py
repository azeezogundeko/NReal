# Auto-generated Boboyii Workflow Agent
# Generated from: Pre-configured Multilingual Assistant Template

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

@dataclass
class WorkflowState:
    """Manages workflow state and extracted variables"""
    current_node: str = ""
    session_id: str = ""
    source_language: str = ''
    translation_text: str = ''
    initial_request: str = ''
    assistance_type: str = ''
    detected_language: str = ''
    cultural_context: str = ''
    current_language: str = ''
    target_language: str = ''
    requested_language: str = ''
    cultural_topic: str = ''
    translation_type: str = ''
    conversation_topic: str = ''
    cultural_region: str = ''
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    global_variables: Dict[str, str] = field(default_factory=dict)

    def get_variable(self, name: str) -> str:
        return self.global_variables.get(name, getattr(self, name, ""))

    def set_variable(self, name: str, value: str):
        if hasattr(self, name):
            setattr(self, name, value)
            logger.info(f"Set variable {name} = {value}")
        else:
            self.global_variables[name] = value
            logger.info(f"Set global variable {name} = {value}")

    def add_to_history(self, role: str, content: str):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": str(asyncio.get_event_loop().time())
        })

    def format_prompt_template(self, template: str) -> str:
        import datetime
        result = template
        now = datetime.datetime.now()
        global_replacements = {
            "now": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
        }
        global_replacements.update(self.global_variables)
        for var_name in re.findall(r'\{\{(\w+(?:\.\w+)*)\}\}', template):
            value = global_replacements.get(var_name, self.get_variable(var_name))
            result = result.replace(f"{{{{{var_name}}}}}", str(value))
        return result

class VariableExtractor:
    """Extracts variables from user responses using LLM"""
    def __init__(self, llm_client):
        self.llm = llm_client

    async def extract_variables(self, user_message: str, extraction_plan: Dict) -> Dict[str, str]:
        if not extraction_plan or "output" not in extraction_plan:
            return {}
        variables_to_extract = extraction_plan["output"]
        if not variables_to_extract:
            return {}
        var_descriptions = [f"- {var['title']}: {var['description']}" for var in variables_to_extract]
        extraction_prompt = f"""
        Extract the following variables from the user's message: "{user_message}"
        Variables to extract:
        {chr(10).join(var_descriptions)}
        Return a JSON object with variable names as keys and extracted values as strings.
        If a variable cannot be determined, use an empty string. Return only valid JSON.
        """
        try:
            response = await self.llm.achat(messages=[ChatMessage(role="user", content=extraction_prompt)])
            extracted = json.loads(response.message.content)
            valid_vars = {var["title"]: str(extracted[var["title"]]) for var in variables_to_extract if var["title"] in extracted and extracted[var["title"]]}
            return valid_vars
        except Exception as e:
            logger.warning(f"Variable extraction failed: {e}")
            return {}

class TransitionEvaluator:
    """Evaluates AI-based transition conditions"""
    def __init__(self, llm_client):
        self.llm = llm_client

    async def should_transition(self, condition_prompt: str, user_message: str, conversation_history: List[Dict]) -> bool:
        context_messages = [f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:]]
        evaluation_prompt = f"""
        Based on the conversation and user's message, is the following condition met?
        CONDITION: {condition_prompt}
        CONVERSATION:
        {chr(10).join(context_messages)}
        USER'S MESSAGE: {user_message}
        Respond with exactly "TRUE" or "FALSE".
        """
        try:
            response = await self.llm.achat(messages=[ChatMessage(role="user", content=evaluation_prompt)])
            return response.message.content.strip().upper() == "TRUE"
        except Exception as e:
            logger.warning(f"Transition evaluation failed: {e}")
            return False

class ProviderConfigManager:
    """Manages dynamic AI provider configurations"""
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

async def handle_welcome_hub(state: WorkflowState, user_message: str, llm_client, variable_extractor: VariableExtractor, transition_evaluator: TransitionEvaluator, provider_config: ProviderConfigManager) -> Optional[Tuple[str, Any]]:
    """Handle welcome_hub conversation node"""
    logger.info(f"Handling welcome_hub node")
    state.current_node = "welcome_hub"
    state.add_to_history("user", user_message)
    
    transitions = [('User chooses English or responds in English', "english_assistant"), ('User chooses Yoruba or responds in Yoruba', "yoruba_assistant"), ('User chooses Hausa or responds in Hausa', "hausa_assistant"), ('User chooses Igbo or responds in Igbo', "igbo_assistant")]
    for edge_condition, target_node in transitions:
        if await transition_evaluator.should_transition(edge_condition, user_message, state.conversation_history):
            state.current_node = target_node
            logger.info(f"Transitioning from welcome_hub to {target_node}")
            # Return a message indicating transition, as the new node will be handled in the next turn
            return (f"Transitioning to {target_node}", provider_config.get_tts_client())

    if True:
        extracted_vars = await variable_extractor.extract_variables(user_message, {"output": [{"type": "string", "title": "detected_language", "description": "The language chosen or detected from user input"}, {"type": "string", "title": "initial_request", "description": "Any initial request or question from the user"}]})
        for var_name, var_value in extracted_vars.items():
            state.set_variable(var_name, var_value)

    node_llm_config = None
    node_llm_client = provider_config.get_llm_client(node_llm_config)

    node_voice_config = None
    tts_client = provider_config.get_tts_client(node_voice_config)

    global_prompt = 'You are a helpful AI assistant with dedicated language-specific nodes. Each language node has pre-configured voice settings and cultural context. You can provide assistance, translations, and information while maintaining authentic communication in Yoruba, Hausa, Igbo, and English.'
    node_prompt = 'Welcome users in all languages and let them choose their preferred language:\n\n\'Hello! Sannu! Ndewo! E ku aaro! \n\nWelcome to your multilingual assistant! Choose your language:\n- English (Press 1 or say "English")\n- Yoruba (Press 2 or say "Yoruba/Ede Yoruba")\n- Hausa (Press 3 or say "Hausa")\n- Igbo (Press 4 or say "Igbo/Asụsụ Igbo")\n\nOr just start speaking in your preferred language and I\'ll detect it!\''
    instruction = "\n\nIMPORTANT: Your reply must be very short and conversational."
    combined_prompt = f"{global_prompt}\n\n--- Node Instructions ---\n{node_prompt} {instruction}"
    formatted_prompt = state.format_prompt_template(combined_prompt)
    
    context_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in state.conversation_history[-10:]]
    context_messages.insert(0, ChatMessage(role="system", content=formatted_prompt))
    
    try:
        response = await node_llm_client.achat(messages=context_messages)
        ai_response = response.message.content
        state.add_to_history("assistant", ai_response)
        logger.info(f"Generated response for welcome_hub: {ai_response[:100]}...")
        return (ai_response, tts_client)
    except Exception as e:
        logger.error(f"Error in welcome_hub: {e}")
        return ("I'm having trouble processing that right now.", tts_client)

async def handle_english_assistant(state: WorkflowState, user_message: str, llm_client, variable_extractor: VariableExtractor, transition_evaluator: TransitionEvaluator, provider_config: ProviderConfigManager) -> Optional[Tuple[str, Any]]:
    """Handle english_assistant conversation node"""
    logger.info(f"Handling english_assistant node")
    state.current_node = "english_assistant"
    state.add_to_history("user", user_message)
    
    transitions = [('User continues conversation in English', "english_assistant"), ('User requests translation services', "translation_hub"), ('User asks about culture, traditions, or regional topics', "cultural_information_hub"), ('User indicates they want to end the conversation', "farewell_hub")]
    for edge_condition, target_node in transitions:
        if await transition_evaluator.should_transition(edge_condition, user_message, state.conversation_history):
            state.current_node = target_node
            logger.info(f"Transitioning from english_assistant to {target_node}")
            # Return a message indicating transition, as the new node will be handled in the next turn
            return (f"Transitioning to {target_node}", provider_config.get_tts_client())

    if True:
        extracted_vars = await variable_extractor.extract_variables(user_message, {"output": [{"type": "string", "title": "current_language", "value": "English", "description": "Current active language"}, {"type": "string", "title": "conversation_topic", "description": "Main topic of conversation"}, {"type": "string", "title": "assistance_type", "description": "Type of assistance provided (information, translation, general help, etc.)"}]})
        for var_name, var_value in extracted_vars.items():
            state.set_variable(var_name, var_value)

    node_llm_config = None
    node_llm_client = provider_config.get_llm_client(node_llm_config)

    node_voice_config = None
    tts_client = provider_config.get_tts_client(node_voice_config)

    global_prompt = 'You are a helpful AI assistant with dedicated language-specific nodes. Each language node has pre-configured voice settings and cultural context. You can provide assistance, translations, and information while maintaining authentic communication in Yoruba, Hausa, Igbo, and English.'
    node_prompt = 'You are now in English mode. Provide helpful assistance in clear, professional English. Handle general questions, provide information, help with tasks, offer translations to other languages, and engage in natural conversation. Use American English conventions and be friendly yet professional.'
    instruction = "\n\nIMPORTANT: Your reply must be very short and conversational."
    combined_prompt = f"{global_prompt}\n\n--- Node Instructions ---\n{node_prompt} {instruction}"
    formatted_prompt = state.format_prompt_template(combined_prompt)
    
    context_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in state.conversation_history[-10:]]
    context_messages.insert(0, ChatMessage(role="system", content=formatted_prompt))
    
    try:
        response = await node_llm_client.achat(messages=context_messages)
        ai_response = response.message.content
        state.add_to_history("assistant", ai_response)
        logger.info(f"Generated response for english_assistant: {ai_response[:100]}...")
        return (ai_response, tts_client)
    except Exception as e:
        logger.error(f"Error in english_assistant: {e}")
        return ("I'm having trouble processing that right now.", tts_client)

async def handle_yoruba_assistant(state: WorkflowState, user_message: str, llm_client, variable_extractor: VariableExtractor, transition_evaluator: TransitionEvaluator, provider_config: ProviderConfigManager) -> Optional[Tuple[str, Any]]:
    """Handle yoruba_assistant conversation node"""
    logger.info(f"Handling yoruba_assistant node")
    state.current_node = "yoruba_assistant"
    state.add_to_history("user", user_message)
    
    transitions = [('User continues conversation in Yoruba', "yoruba_assistant"), ('User requests translation services', "translation_hub"), ('User asks about culture, traditions, or regional topics', "cultural_information_hub"), ('User indicates they want to end the conversation', "farewell_hub")]
    for edge_condition, target_node in transitions:
        if await transition_evaluator.should_transition(edge_condition, user_message, state.conversation_history):
            state.current_node = target_node
            logger.info(f"Transitioning from yoruba_assistant to {target_node}")
            # Return a message indicating transition, as the new node will be handled in the next turn
            return (f"Transitioning to {target_node}", provider_config.get_tts_client())

    if True:
        extracted_vars = await variable_extractor.extract_variables(user_message, {"output": [{"type": "string", "title": "current_language", "value": "Yoruba", "description": "Current active language"}, {"type": "string", "title": "conversation_topic", "description": "Koko oro ibaraenisepo (main conversation topic)"}, {"type": "string", "title": "cultural_context", "value": "yoruba_traditional", "description": "Cultural context for responses"}]})
        for var_name, var_value in extracted_vars.items():
            state.set_variable(var_name, var_value)

    node_llm_config = None
    node_llm_client = provider_config.get_llm_client(node_llm_config)

    node_voice_config = None
    tts_client = provider_config.get_tts_client(node_voice_config)

    global_prompt = 'You are a helpful AI assistant with dedicated language-specific nodes. Each language node has pre-configured voice settings and cultural context. You can provide assistance, translations, and information while maintaining authentic communication in Yoruba, Hausa, Igbo, and English.'
    node_prompt = "O ti wa ni ipo Yoruba bayi. Pese iranwo ni ede Yoruba ti o ye kooro. Lo awon oro ti o t\u1ecd bi '\u1eb9 j\u1ecdw\u1ecd' (please), '\u1eb9 \u1e63e' (thank you), 'bawo ni' (how are you). Ran awon eniyan lowo pelu awon ibeere, fun ni alaye, \u1e63e atum\u1ecd si awon ede miiran, ati \u1e62IS oro tabi gbogbo iru i\u1e63e ti won ba beere. J\u1eb9 ki ibaraenisepo r\u1eb9 j\u1eb9 atun\u1e63e ati ki o ni it\u1ecdju."
    instruction = "\n\nIMPORTANT: Your reply must be very short and conversational."
    combined_prompt = f"{global_prompt}\n\n--- Node Instructions ---\n{node_prompt} {instruction}"
    formatted_prompt = state.format_prompt_template(combined_prompt)
    
    context_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in state.conversation_history[-10:]]
    context_messages.insert(0, ChatMessage(role="system", content=formatted_prompt))
    
    try:
        response = await node_llm_client.achat(messages=context_messages)
        ai_response = response.message.content
        state.add_to_history("assistant", ai_response)
        logger.info(f"Generated response for yoruba_assistant: {ai_response[:100]}...")
        return (ai_response, tts_client)
    except Exception as e:
        logger.error(f"Error in yoruba_assistant: {e}")
        return ("I'm having trouble processing that right now.", tts_client)

async def handle_hausa_assistant(state: WorkflowState, user_message: str, llm_client, variable_extractor: VariableExtractor, transition_evaluator: TransitionEvaluator, provider_config: ProviderConfigManager) -> Optional[Tuple[str, Any]]:
    """Handle hausa_assistant conversation node"""
    logger.info(f"Handling hausa_assistant node")
    state.current_node = "hausa_assistant"
    state.add_to_history("user", user_message)
    
    transitions = [('User continues conversation in Hausa', "hausa_assistant"), ('User requests translation services', "translation_hub"), ('User asks about culture, traditions, or regional topics', "cultural_information_hub"), ('User indicates they want to end the conversation', "farewell_hub")]
    for edge_condition, target_node in transitions:
        if await transition_evaluator.should_transition(edge_condition, user_message, state.conversation_history):
            state.current_node = target_node
            logger.info(f"Transitioning from hausa_assistant to {target_node}")
            # Return a message indicating transition, as the new node will be handled in the next turn
            return (f"Transitioning to {target_node}", provider_config.get_tts_client())

    if True:
        extracted_vars = await variable_extractor.extract_variables(user_message, {"output": [{"type": "string", "title": "current_language", "value": "Hausa", "description": "Current active language"}, {"type": "string", "title": "conversation_topic", "description": "Babban batun hira (main conversation topic)"}, {"type": "string", "title": "cultural_context", "value": "hausa_traditional", "description": "Cultural context for responses"}]})
        for var_name, var_value in extracted_vars.items():
            state.set_variable(var_name, var_value)

    node_llm_config = None
    node_llm_client = provider_config.get_llm_client(node_llm_config)

    node_voice_config = None
    tts_client = provider_config.get_tts_client(node_voice_config)

    global_prompt = 'You are a helpful AI assistant with dedicated language-specific nodes. Each language node has pre-configured voice settings and cultural context. You can provide assistance, translations, and information while maintaining authentic communication in Yoruba, Hausa, Igbo, and English.'
    node_prompt = "Yanzu kuna cikin yanayin Hausa. Bayar da taimako a cikin Hausa mai kyau. Yi amfani da kalmomi masu dacewa kamar 'don Allah' (please), 'na gode' (thank you), 'sannu da zuwa' (welcome). Taimaka wa mutane da tambayoyi, bayar da bayanai, yi fassara zuwa wasu harsuna, da yin hira akan duk wani batu da suke so. Kasance mai son zuciya kuma mai kulawa."
    instruction = "\n\nIMPORTANT: Your reply must be very short and conversational."
    combined_prompt = f"{global_prompt}\n\n--- Node Instructions ---\n{node_prompt} {instruction}"
    formatted_prompt = state.format_prompt_template(combined_prompt)
    
    context_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in state.conversation_history[-10:]]
    context_messages.insert(0, ChatMessage(role="system", content=formatted_prompt))
    
    try:
        response = await node_llm_client.achat(messages=context_messages)
        ai_response = response.message.content
        state.add_to_history("assistant", ai_response)
        logger.info(f"Generated response for hausa_assistant: {ai_response[:100]}...")
        return (ai_response, tts_client)
    except Exception as e:
        logger.error(f"Error in hausa_assistant: {e}")
        return ("I'm having trouble processing that right now.", tts_client)

async def handle_igbo_assistant(state: WorkflowState, user_message: str, llm_client, variable_extractor: VariableExtractor, transition_evaluator: TransitionEvaluator, provider_config: ProviderConfigManager) -> Optional[Tuple[str, Any]]:
    """Handle igbo_assistant conversation node"""
    logger.info(f"Handling igbo_assistant node")
    state.current_node = "igbo_assistant"
    state.add_to_history("user", user_message)
    
    transitions = [('User continues conversation in Igbo', "igbo_assistant"), ('User requests translation services', "translation_hub"), ('User asks about culture, traditions, or regional topics', "cultural_information_hub"), ('User indicates they want to end the conversation', "farewell_hub")]
    for edge_condition, target_node in transitions:
        if await transition_evaluator.should_transition(edge_condition, user_message, state.conversation_history):
            state.current_node = target_node
            logger.info(f"Transitioning from igbo_assistant to {target_node}")
            # Return a message indicating transition, as the new node will be handled in the next turn
            return (f"Transitioning to {target_node}", provider_config.get_tts_client())

    if True:
        extracted_vars = await variable_extractor.extract_variables(user_message, {"output": [{"type": "string", "title": "current_language", "value": "Igbo", "description": "Current active language"}, {"type": "string", "title": "conversation_topic", "description": "Isi okwu mkpar\u1ecbta \u1ee5ka (main conversation topic)"}, {"type": "string", "title": "cultural_context", "value": "igbo_traditional", "description": "Cultural context for responses"}]})
        for var_name, var_value in extracted_vars.items():
            state.set_variable(var_name, var_value)

    node_llm_config = None
    node_llm_client = provider_config.get_llm_client(node_llm_config)

    node_voice_config = None
    tts_client = provider_config.get_tts_client(node_voice_config)

    global_prompt = 'You are a helpful AI assistant with dedicated language-specific nodes. Each language node has pre-configured voice settings and cultural context. You can provide assistance, translations, and information while maintaining authentic communication in Yoruba, Hausa, Igbo, and English.'
    node_prompt = "Ị n\u1ecd ugbu a n'\u1ecdn\u1ecd\u1ee5 Igbo. Nye enyemaka n'as\u1ee5s\u1ee5 Igbo d\u1ecb mma. Jiri okwu kwes\u1ecbr\u1ecb ekwes\u1ecb d\u1ecb ka 'biko' (please), 'daal\u1ee5' (thank you), 'ndewo' (hello). Nyere nd\u1ecb mmad\u1ee5 aka na aj\u1ee5j\u1ee5 ha, nye ozi, t\u1ee5ghar\u1ecba as\u1ee5s\u1ee5 n'as\u1ee5s\u1ee5 nd\u1ecb \u1ecdz\u1ecd, ma kwur\u1ecbta okwu gbasara ihe \u1ecd b\u1ee5la ha ch\u1ecdr\u1ecd. B\u1ee5r\u1ee5 onye obi\u1ecma ma na-elek\u1ecdta."
    instruction = "\n\nIMPORTANT: Your reply must be very short and conversational."
    combined_prompt = f"{global_prompt}\n\n--- Node Instructions ---\n{node_prompt} {instruction}"
    formatted_prompt = state.format_prompt_template(combined_prompt)
    
    context_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in state.conversation_history[-10:]]
    context_messages.insert(0, ChatMessage(role="system", content=formatted_prompt))
    
    try:
        response = await node_llm_client.achat(messages=context_messages)
        ai_response = response.message.content
        state.add_to_history("assistant", ai_response)
        logger.info(f"Generated response for igbo_assistant: {ai_response[:100]}...")
        return (ai_response, tts_client)
    except Exception as e:
        logger.error(f"Error in igbo_assistant: {e}")
        return ("I'm having trouble processing that right now.", tts_client)

async def handle_translation_hub(state: WorkflowState, user_message: str, llm_client, variable_extractor: VariableExtractor, transition_evaluator: TransitionEvaluator, provider_config: ProviderConfigManager) -> Optional[Tuple[str, Any]]:
    """Handle translation_hub conversation node"""
    logger.info(f"Handling translation_hub node")
    state.current_node = "translation_hub"
    state.add_to_history("user", user_message)
    
    transitions = [('Translation completed, user continues in English context', "english_assistant"), ('Translation completed, user continues in Yoruba context', "yoruba_assistant"), ('Translation completed, user continues in Hausa context', "hausa_assistant"), ('Translation completed, user continues in Igbo context', "igbo_assistant")]
    for edge_condition, target_node in transitions:
        if await transition_evaluator.should_transition(edge_condition, user_message, state.conversation_history):
            state.current_node = target_node
            logger.info(f"Transitioning from translation_hub to {target_node}")
            # Return a message indicating transition, as the new node will be handled in the next turn
            return (f"Transitioning to {target_node}", provider_config.get_tts_client())

    if True:
        extracted_vars = await variable_extractor.extract_variables(user_message, {"output": [{"type": "string", "title": "source_language", "description": "Language translating from"}, {"type": "string", "title": "target_language", "description": "Language translating to"}, {"type": "string", "title": "translation_text", "description": "Text being translated"}, {"type": "string", "title": "translation_type", "description": "Type of translation (word, phrase, sentence, cultural expression)"}]})
        for var_name, var_value in extracted_vars.items():
            state.set_variable(var_name, var_value)

    node_llm_config = None
    node_llm_client = provider_config.get_llm_client(node_llm_config)

    node_voice_config = None
    tts_client = provider_config.get_tts_client(node_voice_config)

    global_prompt = 'You are a helpful AI assistant with dedicated language-specific nodes. Each language node has pre-configured voice settings and cultural context. You can provide assistance, translations, and information while maintaining authentic communication in Yoruba, Hausa, Igbo, and English.'
    node_prompt = "Translation Hub - Handle translation requests between any of the supported languages. Provide accurate translations with cultural context. Current language context: {{current_language}}. \n\nFor translations:\n- Explain cultural nuances when needed\n- Provide alternative expressions if direct translation isn't ideal\n- Offer pronunciation help\n- Give context about when to use certain phrases\n\nRespond in the user's current language setting."
    instruction = "\n\nIMPORTANT: Your reply must be very short and conversational."
    combined_prompt = f"{global_prompt}\n\n--- Node Instructions ---\n{node_prompt} {instruction}"
    formatted_prompt = state.format_prompt_template(combined_prompt)
    
    context_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in state.conversation_history[-10:]]
    context_messages.insert(0, ChatMessage(role="system", content=formatted_prompt))
    
    try:
        response = await node_llm_client.achat(messages=context_messages)
        ai_response = response.message.content
        state.add_to_history("assistant", ai_response)
        logger.info(f"Generated response for translation_hub: {ai_response[:100]}...")
        return (ai_response, tts_client)
    except Exception as e:
        logger.error(f"Error in translation_hub: {e}")
        return ("I'm having trouble processing that right now.", tts_client)

async def handle_cultural_information_hub(state: WorkflowState, user_message: str, llm_client, variable_extractor: VariableExtractor, transition_evaluator: TransitionEvaluator, provider_config: ProviderConfigManager) -> Optional[Tuple[str, Any]]:
    """Handle cultural_information_hub conversation node"""
    logger.info(f"Handling cultural_information_hub node")
    state.current_node = "cultural_information_hub"
    state.add_to_history("user", user_message)
    
    transitions = [('Cultural information provided, user continues in English context', "english_assistant"), ('Cultural information provided, user continues in Yoruba context', "yoruba_assistant"), ('Cultural information provided, user continues in Hausa context', "hausa_assistant"), ('Cultural information provided, user continues in Igbo context', "igbo_assistant")]
    for edge_condition, target_node in transitions:
        if await transition_evaluator.should_transition(edge_condition, user_message, state.conversation_history):
            state.current_node = target_node
            logger.info(f"Transitioning from cultural_information_hub to {target_node}")
            # Return a message indicating transition, as the new node will be handled in the next turn
            return (f"Transitioning to {target_node}", provider_config.get_tts_client())

    if True:
        extracted_vars = await variable_extractor.extract_variables(user_message, {"output": [{"type": "string", "title": "cultural_topic", "description": "Specific cultural topic being discussed"}, {"type": "string", "title": "cultural_region", "description": "Specific region or ethnic group focus"}]})
        for var_name, var_value in extracted_vars.items():
            state.set_variable(var_name, var_value)

    node_llm_config = None
    node_llm_client = provider_config.get_llm_client(node_llm_config)

    node_voice_config = None
    tts_client = provider_config.get_tts_client(node_voice_config)

    global_prompt = 'You are a helpful AI assistant with dedicated language-specific nodes. Each language node has pre-configured voice settings and cultural context. You can provide assistance, translations, and information while maintaining authentic communication in Yoruba, Hausa, Igbo, and English.'
    node_prompt = "Cultural Information Hub - Provide culturally relevant information based on current language context: {{current_language}} with cultural context: {{cultural_context}}.\n\nShare authentic information about:\n- Festivals and celebrations\n- Traditional foods and recipes\n- Music and dance\n- History and customs\n- Proverbs and sayings\n- Regional variations\n\nRespond in the user's current language with appropriate cultural sensitivity."
    instruction = "\n\nIMPORTANT: Your reply must be very short and conversational."
    combined_prompt = f"{global_prompt}\n\n--- Node Instructions ---\n{node_prompt} {instruction}"
    formatted_prompt = state.format_prompt_template(combined_prompt)
    
    context_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in state.conversation_history[-10:]]
    context_messages.insert(0, ChatMessage(role="system", content=formatted_prompt))
    
    try:
        response = await node_llm_client.achat(messages=context_messages)
        ai_response = response.message.content
        state.add_to_history("assistant", ai_response)
        logger.info(f"Generated response for cultural_information_hub: {ai_response[:100]}...")
        return (ai_response, tts_client)
    except Exception as e:
        logger.error(f"Error in cultural_information_hub: {e}")
        return ("I'm having trouble processing that right now.", tts_client)

async def handle_language_switch_hub(state: WorkflowState, user_message: str, llm_client, variable_extractor: VariableExtractor, transition_evaluator: TransitionEvaluator, provider_config: ProviderConfigManager) -> Optional[Tuple[str, Any]]:
    """Handle language_switch_hub conversation node"""
    logger.info(f"Handling language_switch_hub node")
    state.current_node = "language_switch_hub"
    state.add_to_history("user", user_message)
    
    transitions = [('User requests switch to English', "english_assistant"), ('User requests switch to Yoruba', "yoruba_assistant"), ('User requests switch to Hausa', "hausa_assistant"), ('User requests switch to Igbo', "igbo_assistant")]
    for edge_condition, target_node in transitions:
        if await transition_evaluator.should_transition(edge_condition, user_message, state.conversation_history):
            state.current_node = target_node
            logger.info(f"Transitioning from language_switch_hub to {target_node}")
            # Return a message indicating transition, as the new node will be handled in the next turn
            return (f"Transitioning to {target_node}", provider_config.get_tts_client())

    if True:
        extracted_vars = await variable_extractor.extract_variables(user_message, {"output": [{"type": "string", "title": "requested_language", "description": "The new language user wants to switch to"}]})
        for var_name, var_value in extracted_vars.items():
            state.set_variable(var_name, var_value)

    node_llm_config = None
    node_llm_client = provider_config.get_llm_client(node_llm_config)

    node_voice_config = None
    tts_client = provider_config.get_tts_client(node_voice_config)

    global_prompt = 'You are a helpful AI assistant with dedicated language-specific nodes. Each language node has pre-configured voice settings and cultural context. You can provide assistance, translations, and information while maintaining authentic communication in Yoruba, Hausa, Igbo, and English.'
    node_prompt = "Language Switch Hub - Handle requests to change language. Current language: {{current_language}}.\n\nConfirm the switch and route to appropriate language node:\n- English: 'Switching to English. How can I help you?'\n- Yoruba: 'Mo ti yi pada si ede Yoruba. Bawo ni mo se le ran yin lowo?'\n- Hausa: 'Na canja zuwa Hausa. Yaya zan iya taimaka maku?'\n- Igbo: 'Agbanwere m gaa Igbo. Kedu ka m ga-esi nyere g\u1ecb aka?'"
    instruction = "\n\nIMPORTANT: Your reply must be very short and conversational."
    combined_prompt = f"{global_prompt}\n\n--- Node Instructions ---\n{node_prompt} {instruction}"
    formatted_prompt = state.format_prompt_template(combined_prompt)
    
    context_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in state.conversation_history[-10:]]
    context_messages.insert(0, ChatMessage(role="system", content=formatted_prompt))
    
    try:
        response = await node_llm_client.achat(messages=context_messages)
        ai_response = response.message.content
        state.add_to_history("assistant", ai_response)
        logger.info(f"Generated response for language_switch_hub: {ai_response[:100]}...")
        return (ai_response, tts_client)
    except Exception as e:
        logger.error(f"Error in language_switch_hub: {e}")
        return ("I'm having trouble processing that right now.", tts_client)

async def handle_help_limitations(state: WorkflowState, user_message: str, llm_client, variable_extractor: VariableExtractor, transition_evaluator: TransitionEvaluator, provider_config: ProviderConfigManager) -> Optional[Tuple[str, Any]]:
    """Handle help_limitations conversation node"""
    logger.info(f"Handling help_limitations node")
    state.current_node = "help_limitations"
    state.add_to_history("user", user_message)
    
    transitions = [('Limitations explained, user continues in English context', "english_assistant"), ('Limitations explained, user continues in Yoruba context', "yoruba_assistant"), ('Limitations explained, user continues in Hausa context', "hausa_assistant"), ('Limitations explained, user continues in Igbo context', "igbo_assistant")]
    for edge_condition, target_node in transitions:
        if await transition_evaluator.should_transition(edge_condition, user_message, state.conversation_history):
            state.current_node = target_node
            logger.info(f"Transitioning from help_limitations to {target_node}")
            # Return a message indicating transition, as the new node will be handled in the next turn
            return (f"Transitioning to {target_node}", provider_config.get_tts_client())

    if False:
        extracted_vars = await variable_extractor.extract_variables(user_message, None)
        for var_name, var_value in extracted_vars.items():
            state.set_variable(var_name, var_value)

    node_llm_config = None
    node_llm_client = provider_config.get_llm_client(node_llm_config)

    node_voice_config = None
    tts_client = provider_config.get_tts_client(node_voice_config)

    global_prompt = 'You are a helpful AI assistant with dedicated language-specific nodes. Each language node has pre-configured voice settings and cultural context. You can provide assistance, translations, and information while maintaining authentic communication in Yoruba, Hausa, Igbo, and English.'
    node_prompt = "Handle limitations based on current language ({{current_language}}):\n\nEnglish: 'I understand what you're looking for, but that's outside my current capabilities. However, I can help you with general questions, translations between Yoruba, Hausa, Igbo and English, cultural information, or other assistance.'\n\nYoruba: 'Mo ye ohun ti o n wa, \u1e63ugb\u1ecdn eyi ko si laarin aw\u1ecdn agbara mi l\u1ecdw\u1ecd. Sib\u1eb9sib\u1eb9, mo le ran \u1ecd lowo pelu aw\u1ecdn ibeere gbogbogbo, atum\u1ecd laarin Yoruba, Hausa, Igbo ati English, alaye asa, tabi iranwo miiran.'\n\nHausa: 'Na gane abin da kuke nema, amma wannan bai shiga cikin iyawata ba a yanzu. Duk da haka, zan iya taimaka maku da tambayoyi na gaba\u0257aya, fassara tsakanin Yoruba, Hausa, Igbo da Turanci, bayanan al'adu, ko wasu taimako.'\n\nIgbo: 'Agh\u1ecdtara m ihe \u1ecbna-ach\u1ecd, mana nke ah\u1ee5 ab\u1ee5gh\u1ecb ihe m nwere ike ime ugbu a. Ot\u00fa \u1ecd d\u1ecb, enwere m ike inyere g\u1ecb aka na aj\u1ee5j\u1ee5 izugbe, nt\u1ee5ghar\u1ecb n'etiti Yoruba, Hausa, Igbo na Bekee, ozi omenala, ma \u1ecd b\u1ee5 enyemaka nd\u1ecb \u1ecdz\u1ecd.'"
    instruction = "\n\nIMPORTANT: Your reply must be very short and conversational."
    combined_prompt = f"{global_prompt}\n\n--- Node Instructions ---\n{node_prompt} {instruction}"
    formatted_prompt = state.format_prompt_template(combined_prompt)
    
    context_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in state.conversation_history[-10:]]
    context_messages.insert(0, ChatMessage(role="system", content=formatted_prompt))
    
    try:
        response = await node_llm_client.achat(messages=context_messages)
        ai_response = response.message.content
        state.add_to_history("assistant", ai_response)
        logger.info(f"Generated response for help_limitations: {ai_response[:100]}...")
        return (ai_response, tts_client)
    except Exception as e:
        logger.error(f"Error in help_limitations: {e}")
        return ("I'm having trouble processing that right now.", tts_client)

async def handle_farewell_hub(state: WorkflowState, user_message: str, llm_client, variable_extractor: VariableExtractor, transition_evaluator: TransitionEvaluator, provider_config: ProviderConfigManager) -> Optional[Tuple[str, Any]]:
    """Handle farewell_hub conversation node"""
    logger.info(f"Handling farewell_hub node")
    state.current_node = "farewell_hub"
    state.add_to_history("user", user_message)
    
    transitions = []
    for edge_condition, target_node in transitions:
        if await transition_evaluator.should_transition(edge_condition, user_message, state.conversation_history):
            state.current_node = target_node
            logger.info(f"Transitioning from farewell_hub to {target_node}")
            # Return a message indicating transition, as the new node will be handled in the next turn
            return (f"Transitioning to {target_node}", provider_config.get_tts_client())

    if False:
        extracted_vars = await variable_extractor.extract_variables(user_message, None)
        for var_name, var_value in extracted_vars.items():
            state.set_variable(var_name, var_value)

    node_llm_config = None
    node_llm_client = provider_config.get_llm_client(node_llm_config)

    node_voice_config = None
    tts_client = provider_config.get_tts_client(node_voice_config)

    global_prompt = 'You are a helpful AI assistant with dedicated language-specific nodes. Each language node has pre-configured voice settings and cultural context. You can provide assistance, translations, and information while maintaining authentic communication in Yoruba, Hausa, Igbo, and English.'
    node_prompt = "Provide warm farewell based on current language ({{current_language}}):\n\nEnglish: 'Thank you for using our multilingual assistant! I hope I was able to help you today. Have a wonderful day!'\n\nYoruba: 'E \u1e63e fun lilo iranwo wa ti o ni ede pup\u1ecd! Mo nireti pe mo le ran yin lowo loni. E ni \u1ecdj\u1ecd ti o dara!'\n\nHausa: 'Na gode da yin amfani da mataimakin mu mai harsuna da yawa! Ina fatan na iya taimaka maku a yau. Ku yi kyakkyawan rana!'\n\nIgbo: 'Daal\u1ee5 maka iji onyeinyeaka any\u1ecb nwere as\u1ee5s\u1ee5 d\u1ecb iche iche! Echere m na m nwere ike inyere g\u1ecb aka taa. Nwee \u1ecdmar\u1ecbcha \u1ee5b\u1ecdch\u1ecb!'"
    instruction = "\n\nIMPORTANT: Your reply must be very short and conversational."
    combined_prompt = f"{global_prompt}\n\n--- Node Instructions ---\n{node_prompt} {instruction}"
    formatted_prompt = state.format_prompt_template(combined_prompt)
    
    context_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in state.conversation_history[-10:]]
    context_messages.insert(0, ChatMessage(role="system", content=formatted_prompt))
    
    try:
        response = await node_llm_client.achat(messages=context_messages)
        ai_response = response.message.content
        state.add_to_history("assistant", ai_response)
        logger.info(f"Generated response for farewell_hub: {ai_response[:100]}...")
        return (ai_response, tts_client)
    except Exception as e:
        logger.error(f"Error in farewell_hub: {e}")
        return ("I'm having trouble processing that right now.", tts_client)

class PreConfiguredMultilingualAssistantTemplateAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = WorkflowState()
        self.variable_extractor = None
        self.transition_evaluator = None
        self.provider_config = None
        self.handler_map = {}
        self.current_session = None
        self.room = None

    async def start(self, session: AgentSession):
        self.state.session_id = session.id
        logger.info(f"Starting PreConfiguredMultilingualAssistantTemplateAgent with session {self.state.session_id}")
        initial_message = await self.get_initial_message()
        if initial_message:
            await session.say(initial_message)

    def set_handlers(self, handlers: Dict[str, callable]):
        self.handler_map = handlers

    async def recreate_session_with_node_config(self, node_name: str, llm_client):
        """Recreate the session with node-specific TTS/STT/LLM configuration"""
        if not self.room:
            logger.error("No room available for session recreation")
            return None
            
        # Get node-specific configurations
        node_obj = next((n for n in workflow_nodes if n['name'] == node_name), None)
        if not node_obj:
            logger.error(f"Node {node_name} not found in workflow_nodes")
            return None
            
        # Get node-specific configs (these can be customized per node)
        node_llm_config = node_obj.get('llm_config', {})
        node_voice_config = node_obj.get('voice_config', {})
        node_transcriber_config = node_obj.get('transcriber_config', {})
        
        # Create clients with node-specific configs
        stt_client = self.provider_config.get_stt_client(node_transcriber_config)
        tts_client = self.provider_config.get_tts_client(node_voice_config)
        node_llm_client = self.provider_config.get_llm_client(node_llm_config)
        vad_client = silero.VAD.load()
        
        # Create new session with node-specific clients
        new_session = AgentSession(
            stt=stt_client,
            llm=node_llm_client,  # Use node-specific LLM
            tts=tts_client,       # Use node-specific TTS
            vad=vad_client,
            # agent=self,
        )
        
        # Set up event handlers for the new session
        @new_session.on("user_speech_committed")
        async def on_user_speech(ev):
            user_message = ev.user_transcript
            logger.info(f"User said: {user_message}")
            response_text, _ = await self.process_workflow_message(user_message, node_llm_client)
            if response_text:
                await new_session.say(response_text)
                logger.info(f"Agent responded: {response_text[:100]}...")
        
        # Close old session if it exists
        if self.current_session:
            try:
                await self.current_session.close()
            except Exception as e:
                logger.warning(f"Error closing old session: {e}")
        
        # Start new session
        await new_session.start(self.room)
        self.current_session = new_session
        
        logger.info(f"Recreated session for node {node_name} with custom TTS/STT/LLM")
        return new_session

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
            self.state.current_node = "welcome_hub"
        
        current_node_name = self.state.current_node
        handler = self.handler_map.get(current_node_name)
        
        if not handler:
            logger.error(f"No handler for node: {current_node_name}")
            return ("I have a technical issue.", None)

        node_obj = next((n for n in workflow_nodes if n['name'] == current_node_name), None)
        if not node_obj:
            return (f"Configuration for node {current_node_name} not found.", None)

        try:
            if node_obj['type'] == 'conversation':
                response, tts_client = await handler(
                    self.state, user_message, llm_client, self.variable_extractor, self.transition_evaluator, self.provider_config
                )
                
                # Check if a transition occurred and recreate session if needed
                if self.state.current_node != current_node_name:
                    logger.info(f"Node transition detected: {current_node_name} -> {self.state.current_node}")
                    # Recreate session with new node's TTS/STT/LLM configuration
                    await self.recreate_session_with_node_config(self.state.current_node, llm_client)
                
                return response, tts_client
            elif node_obj['type'] == 'tool':
                tool_response = await handler(self.state)
                return tool_response, self.provider_config.get_tts_client() # Use default TTS for tool responses
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return ("I encountered an error.", None)
        return ("No response generated.", None)

    async def get_initial_message(self) -> str:
        start_node_data = next((n for n in workflow_nodes if n.get('is_start')), None)
        if start_node_data and start_node_data.get('message_plan', {}).get('firstMessage'):
            msg = start_node_data['message_plan']['firstMessage']
            self.state.add_to_history("assistant", msg)
            return msg
        return "Hello! How can I help you today?"

workflow_nodes = [
    {
        'name': 'welcome_hub', 
        'type': 'conversation', 
        'prompt': 'Welcome users in all languages and let them choose their preferred language:\n\n\'Hello! Sannu! Ndewo! E ku aaro! \n\nWelcome to your multilingual assistant! Choose your language:\n- English (Press 1 or say "English")\n- Yoruba (Press 2 or say "Yoruba/Ede Yoruba")\n- Hausa (Press 3 or say "Hausa")\n- Igbo (Press 4 or say "Igbo/Asụsụ Igbo")\n\nOr just start speaking in your preferred language and I\'ll detect it!\'', 
        'message_plan': {'firstMessage': "Hello! Sannu! Ndewo! E ku aaro! Choose your language or start speaking, and I'll assist you!"}, 
        'is_start': True, 
        'voice_config': {'provider': 'deepgram', 'model': 'aura-2-luna-en'}, 
        'llm_config': {'provider': 'openai', 'model': 'gpt-4o'},
        'transcriber_config': {'provider': 'deepgram', 'model': 'nova-2'}
    },
    {
        'name': 'english_assistant', 
        'type': 'conversation', 
        'prompt': 'You are now in English mode. Provide helpful assistance in clear, professional English. Handle general questions, provide information, help with tasks, offer translations to other languages, and engage in natural conversation. Use American English conventions and be friendly yet professional.', 
        'message_plan': None, 
        'is_start': False, 
        'voice_config': {'provider': 'deepgram', 'model': 'aura-2-luna-en'}, 
        'llm_config': {'provider': 'openai', 'model': 'gpt-4o'},
        'transcriber_config': {'provider': 'deepgram', 'model': 'nova-2'}
    },
    {
        'name': 'yoruba_assistant', 
        'type': 'conversation', 
        'prompt': "O ti wa ni ipo Yoruba bayi. Pese iranwo ni ede Yoruba ti o ye kooro. Lo awon oro ti o t\u1ecd bi '\u1eb9 j\u1ecdw\u1ecd' (please), '\u1eb9 \u1e63e' (thank you), 'bawo ni' (how are you). Ran awon eniyan lowo pelu awon ibeere, fun ni alaye, \u1e63e atum\u1ecd si awon ede miiran, ati \u1e62IS oro tabi gbogbo iru i\u1e63e ti won ba beere. J\u1eb9 ki ibaraenisepo r\u1eb9 j\u1eb9 atun\u1e63e ati ki o ni it\u1ecdju.", 
        'message_plan': None, 
        'is_start': False, 
        'voice_config': {'provider': 'deepgram', 'model': 'aura-2-stella-en'},  # Different voice for Yoruba
        'llm_config': {'provider': 'openai', 'model': 'gpt-4o'},
        'transcriber_config': {'provider': 'deepgram', 'model': 'nova-2'}
    },
    {
        'name': 'hausa_assistant', 
        'type': 'conversation', 
        'prompt': "Yanzu kuna cikin yanayin Hausa. Bayar da taimako a cikin Hausa mai kyau. Yi amfani da kalmomi masu dacewa kamar 'don Allah' (please), 'na gode' (thank you), 'sannu da zuwa' (welcome). Taimaka wa mutane da tambayoyi, bayar da bayanai, yi fassara zuwa wasu harsuna, da yin hira akan duk wani batu da suke so. Kasance mai son zuciya kuma mai kulawa.", 
        'message_plan': None, 
        'is_start': False, 
        'voice_config': {'provider': 'deepgram', 'model': 'aura-2-orion-en'},  # Different voice for Hausa
        'llm_config': {'provider': 'openai', 'model': 'gpt-4o'},
        'transcriber_config': {'provider': 'deepgram', 'model': 'nova-2'}
    },
    {
        'name': 'igbo_assistant', 
        'type': 'conversation', 
        'prompt': "Ị n\u1ecd ugbu a n'\u1ecdn\u1ecd\u1ee5 Igbo. Nye enyemaka n'as\u1ee5s\u1ee5 Igbo d\u1ecb mma. Jiri okwu kwes\u1ecbr\u1ecb ekwes\u1ecb d\u1ecb ka 'biko' (please), 'daal\u1ee5' (thank you), 'ndewo' (hello). Nyere nd\u1ecb mmad\u1ee5 aka na aj\u1ee5j\u1ee5 ha, nye ozi, t\u1ee5ghar\u1ecba as\u1ee5s\u1ee5 n'as\u1ee5s\u1ee5 nd\u1ecb \u1ecdz\u1ecd, ma kwur\u1ecbta okwu gbasara ihe \u1ecd b\u1ee5la ha ch\u1ecdr\u1ecd. B\u1ee5r\u1ee5 onye obi\u1ecma ma na-elek\u1ecdta.", 
        'message_plan': None, 
        'is_start': False, 
        'voice_config': {'provider': 'deepgram', 'model': 'aura-2-arcas-en'},  # Different voice for Igbo
        'llm_config': {'provider': 'openai', 'model': 'gpt-4o'},
        'transcriber_config': {'provider': 'deepgram', 'model': 'nova-2'}
    },
    {
        'name': 'translation_hub', 
        'type': 'conversation', 
        'prompt': "Translation Hub - Handle translation requests between any of the supported languages. Provide accurate translations with cultural context. Current language context: {{current_language}}. \n\nFor translations:\n- Explain cultural nuances when needed\n- Provide alternative expressions if direct translation isn't ideal\n- Offer pronunciation help\n- Give context about when to use certain phrases\n\nRespond in the user's current language setting.", 
        'message_plan': None, 
        'is_start': False, 
        'voice_config': {'provider': 'deepgram', 'model': 'aura-2-luna-en'}, 
        'llm_config': {'provider': 'openai', 'model': 'gpt-4o'},
        'transcriber_config': {'provider': 'deepgram', 'model': 'nova-2'}
    },
    {
        'name': 'cultural_information_hub', 
        'type': 'conversation', 
        'prompt': "Cultural Information Hub - Provide culturally relevant information based on current language context: {{current_language}} with cultural context: {{cultural_context}}.\n\nShare authentic information about:\n- Festivals and celebrations\n- Traditional foods and recipes\n- Music and dance\n- History and customs\n- Proverbs and sayings\n- Regional variations\n\nRespond in the user's current language with appropriate cultural sensitivity.", 
        'message_plan': None, 
        'is_start': False, 
        'voice_config': {'provider': 'deepgram', 'model': 'aura-2-luna-en'}, 
        'llm_config': {'provider': 'openai', 'model': 'gpt-4o'},
        'transcriber_config': {'provider': 'deepgram', 'model': 'nova-2'}
    },
    {
        'name': 'language_switch_hub', 
        'type': 'conversation', 
        'prompt': "Language Switch Hub - Handle requests to change language. Current language: {{current_language}}.\n\nConfirm the switch and route to appropriate language node:\n- English: 'Switching to English. How can I help you?'\n- Yoruba: 'Mo ti yi pada si ede Yoruba. Bawo ni mo se le ran yin lowo?'\n- Hausa: 'Na canja zuwa Hausa. Yaya zan iya taimaka maku?'\n- Igbo: 'Agbanwere m gaa Igbo. Kedu ka m ga-esi nyere g\u1ecb aka?'", 
        'message_plan': None, 
        'is_start': False, 
        'voice_config': {'provider': 'deepgram', 'model': 'aura-2-luna-en'}, 
        'llm_config': {'provider': 'openai', 'model': 'gpt-4o'},
        'transcriber_config': {'provider': 'deepgram', 'model': 'nova-2'}
    },
    {
        'name': 'help_limitations', 
        'type': 'conversation', 
        'prompt': "Handle limitations based on current language ({{current_language}}):\n\nEnglish: 'I understand what you're looking for, but that's outside my current capabilities. However, I can help you with general questions, translations between Yoruba, Hausa, Igbo and English, cultural information, or other assistance.'\n\nYoruba: 'Mo ye ohun ti o n wa, \u1e63ugb\u1ecdn eyi ko si laarin aw\u1ecdn agbara mi l\u1ecdw\u1ecd. Sib\u1eb9sib\u1eb9, mo le ran \u1ecd lowo pelu aw\u1ecdn ibeere gbogbogbo, atum\u1ecd laarin Yoruba, Hausa, Igbo ati English, alaye asa, tabi iranwo miiran.'\n\nHausa: 'Na gane abin da kuke nema, amma wannan bai shiga cikin iyawata ba a yanzu. Duk da haka, zan iya taimaka maku da tambayoyi na gaba\u0257aya, fassara tsakanin Yoruba, Hausa, Igbo da Turanci, bayanan al'adu, ko wasu taimako.'\n\nIgbo: 'Agh\u1ecdtara m ihe \u1ecbna-ach\u1ecd, mana nke ah\u1ee5 ab\u1ee5gh\u1ecb ihe m nwere ike ime ugbu a. Ot\u00fa \u1ecd d\u1ecb, enwere m ike inyere g\u1ecb aka na aj\u1ee5j\u1ee5 izugbe, nt\u1ee5ghar\u1ecb n'etiti Yoruba, Hausa, Igbo na Bekee, ozi omenala, ma \u1ecd b\u1ee5 enyemaka nd\u1ecb \u1ecdz\u1ecd.'", 
        'message_plan': None, 
        'is_start': False, 
        'voice_config': {'provider': 'deepgram', 'model': 'aura-2-luna-en'}, 
        'llm_config': {'provider': 'openai', 'model': 'gpt-4o'},
        'transcriber_config': {'provider': 'deepgram', 'model': 'nova-2'}
    },
    {
        'name': 'farewell_hub', 
        'type': 'conversation', 
        'prompt': "Provide warm farewell based on current language ({{current_language}}):\n\nEnglish: 'Thank you for using our multilingual assistant! I hope I was able to help you today. Have a wonderful day!'\n\nYoruba: 'E \u1e63e fun lilo iranwo wa ti o ni ede pup\u1ecd! Mo nireti pe mo le ran yin lowo loni. E ni \u1ecdj\u1ecd ti o dara!'\n\nHausa: 'Na gode da yin amfani da mataimakin mu mai harsuna da yawa! Ina fatan na iya taimaka maku a yau. Ku yi kyakkyawan rana!'\n\nIgbo: 'Daal\u1ee5 maka iji onyeinyeaka any\u1ecb nwere as\u1ee5s\u1ee5 d\u1ecb iche iche! Echere m na m nwere ike inyere g\u1ecb aka taa. Nwee \u1ecdmar\u1ecbcha \u1ee5b\u1ecdch\u1ecb!'", 
        'message_plan': None, 
        'is_start': False, 
        'voice_config': {'provider': 'deepgram', 'model': 'aura-2-luna-en'}, 
        'llm_config': {'provider': 'openai', 'model': 'gpt-4o'},
        'transcriber_config': {'provider': 'deepgram', 'model': 'nova-2'}
    }
]

async def entrypoint(ctx: JobContext):
    logger.info(f"Starting Pre-configured Multilingual Assistant Template agent")
    
    # Initialize LLM with a default/fallback
    llm_client = openai.LLM(model="gpt-4o")

    # Initialize agent and its components
    agent = PreConfiguredMultilingualAssistantTemplateAgent()
    agent.room = ctx.room  # Store room reference for session recreation
    
    global_llm_config = {}
    global_voice_config = {}
    global_transcriber_config = {}
    global_variables = {}

    await agent.initialize_components(
        llm_client,
        global_llm_config=global_llm_config,
        global_voice_config=global_voice_config,
        global_transcriber_config=global_transcriber_config,
        global_variables=global_variables
    )
    
    # Dynamically create a map of node names to handler functions
    handler_map = {}
    for node in workflow_nodes:
        func_name = "handle_" + re.sub(r'[^a-zA-Z0-9_]', '_', node['name']).lower()
        if func_name in globals():
            handler_map[node['name']] = globals()[func_name]
    agent.set_handlers(handler_map)

    # Configure initial session with global provider settings
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
        logger.info(f"User said: {user_message}")
        response_text, _ = await agent.process_workflow_message(user_message, llm_client)
        if response_text:
            await session.say(response_text)
            logger.info(f"Agent responded: {response_text[:100]}...")

    await session.start(ctx.room)
    agent.current_session = session  # Store reference to current session

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))