import os
import re
from pathlib import Path
from typing import Generator, List, Dict, Any, Optional
from llama_cpp import Llama
from config import MODELS_DIR, N_CTX, N_THREADS, N_GPU_LAYERS, SECTOR_SYSTEM_PROMPTS, AVAILABLE_MODELS

GREETING_WORDS = {
    "hello", "hi", "hey", "namaste", "namaskar", "good morning", "good evening", 
    "good afternoon", "howdy", "hola", "ram ram", "kisan bhai", "who are you",
    "help", "start", "test"
}

def is_simple_greeting(msg: str) -> bool:
    clean = re.sub(r'[^a-zA-Z\s]', '', msg).strip().lower()
    words = clean.split()
    if not words:
        return True
    if len(words) <= 3 and any(w in GREETING_WORDS for w in words):
        return True
    if clean in GREETING_WORDS:
        return True
    return False

class LocalModelEngine:
    def __init__(self, model_path: Optional[Path] = None):
        self.llm = None
        self.model_path = model_path
        self.model_filename = model_path.name if model_path else None
        self._load_model()

    def _find_model_file(self) -> Path:
        if self.model_path and Path(self.model_path).exists():
            return Path(self.model_path)

        env_model = os.getenv("WEATHERGPT_MODEL")
        if env_model:
            p = Path(env_model)
            if p.exists():
                return p
            p_sub = MODELS_DIR / env_model
            if p_sub.exists():
                return p_sub

        gguf_files = list(MODELS_DIR.glob("*.gguf"))
        if not gguf_files:
            raise FileNotFoundError(
                f"No .gguf model found in {MODELS_DIR}. "
                "Please run `python download_model.py` first to download a model."
            )
        gguf_files.sort(key=lambda p: p.stat().st_size, reverse=True)
        return gguf_files[0]

    def _load_model(self):
        target_path = self._find_model_file()
        self.model_path = target_path
        self.model_filename = target_path.name
        print("\n=======================================================")
        print(f"[ENGINE] Loading local GGUF model: {target_path.name}")
        print(f"[ENGINE] Size: {target_path.stat().st_size / (1024**3):.2f} GB")
        print(f"[ENGINE] Context: {N_CTX} tokens | CPU Threads: {N_THREADS} | GPU Layers: {N_GPU_LAYERS}")
        print("=======================================================\n")
        
        self.llm = Llama(
            model_path=str(target_path),
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False
        )
        print("[ENGINE] Model initialized and ready for offline inference!\n")

    def build_prompt_messages(
        self,
        user_message: str,
        location: str,
        weather_context: str,
        sector_focus: str,
        language: str,
        is_voice_mode: bool,
        is_detail_mode: bool,
        history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        system_base = SECTOR_SYSTEM_PROMPTS.get(sector_focus.lower(), SECTOR_SYSTEM_PROMPTS["general"])
        
        rules = (
            "STRICT CONVERSATIONAL & PROPORTIONALITY RULES:\n"
            "1. PROPORTIONATE BREVITY: Match answer length strictly to the user's inquiry.\n"
            "   - For casual greetings ('hello', 'hi', 'namaste', 'good morning'): Respond warmly in ONLY 1 to 2 sentences. "
            f"Briefly mention current temperature/weather at {location} and ask how you can assist their sector operations today. "
            "STRICTLY FORBIDDEN: Do NOT output checklists, multi-paragraph essays, or unsolicited farming advice when greeted.\n"
            "   - For specific questions (e.g. 'Should I irrigate today?', 'Will it rain at 4 PM?'): "
            "Give a direct clear answer in the first sentence, followed by 2-3 brief supporting bullet points citing relevant Open-Meteo metrics (e.g. soil moisture, ET0, rain probability). "
            "Do NOT mention unrelated topics (e.g., don't discuss harvesting or pesticides if asked about irrigation).\n"
            "   - For comprehensive multi-part queries: Provide a structured, concise response with bullet points (maximum 150-200 words).\n"
            "2. TELEMETRY GROUNDING: Use the provided Open-Meteo readings as absolute scientific ground truth. Cite exact numbers when relevant. Never hallucinate or contradict the telemetry.\n"
            "3. NO REGURGITATION: Do NOT repeat the entire weather data block back to the user. Only reference the metrics that directly impact your advice."
        )

        system_prompt = (
            f"{system_base}\n\n"
            "AUTHORITATIVE LIVE OPEN-METEO METEOROLOGICAL TELEMETRY:\n"
            f"Location: {location}\n"
            f"{weather_context.strip()}\n\n"
            f"{rules}\n"
        )

        if is_voice_mode:
            system_prompt += (
                "4. VOICE AI MODE ACTIVE: "
                "Answer in 1 to 3 spoken sentences maximum. "
                "Never use markdown formatting, asterisks, bullet points, or lists so speech synthesis sounds natural."
            )
        elif is_detail_mode:
            system_prompt += (
                "4. DETAIL MODE REQUESTED: "
                "Provide a comprehensive, structured breakdown with clear section headers and numerical telemetry references."
            )
        else:
            system_prompt += (
                "4. CHAT MODE: Keep responses concise, direct, and actionable."
            )

        messages = [{"role": "system", "content": system_prompt}]

        for item in history[-6:]:
            role = item.get("role", "user")
            content = item.get("content", "")
            if content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})
        return messages

    def stream_completion(
        self,
        user_message: str,
        location: str = "Live Location",
        weather_context: str = "",
        sector_focus: str = "farmer",
        language: str = "en",
        is_voice_mode: bool = False,
        is_detail_mode: bool = False,
        history: List[Dict[str, str]] = None
    ) -> Generator[str, None, None]:
        if not self.llm:
            self._load_model()

        messages = self.build_prompt_messages(
            user_message=user_message,
            location=location,
            weather_context=weather_context,
            sector_focus=sector_focus,
            language=language,
            is_voice_mode=is_voice_mode,
            is_detail_mode=is_detail_mode,
            history=history or []
        )

        greeting = is_simple_greeting(user_message)
        if is_voice_mode:
            max_tokens = 140
            temperature = 0.6
        elif greeting:
            max_tokens = 90
            temperature = 0.5
        elif is_detail_mode:
            max_tokens = 512
            temperature = 0.7
        else:
            max_tokens = 280
            temperature = 0.65

        response = self.llm.create_chat_completion(
            messages=messages,
            stream=True,
            temperature=temperature,
            max_tokens=max_tokens
        )

        for chunk in response:
            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content

    def generate_completion(
        self,
        user_message: str,
        location: str = "Live Location",
        weather_context: str = "",
        sector_focus: str = "farmer",
        language: str = "en",
        is_voice_mode: bool = False,
        is_detail_mode: bool = False,
        history: List[Dict[str, str]] = None
    ) -> str:
        tokens = list(self.stream_completion(
            user_message=user_message,
            location=location,
            weather_context=weather_context,
            sector_focus=sector_focus,
            language=language,
            is_voice_mode=is_voice_mode,
            is_detail_mode=is_detail_mode,
            history=history
        ))
        return "".join(tokens).strip()

_engine_instance: Optional[LocalModelEngine] = None

def get_engine(model_path: Optional[Path] = None) -> LocalModelEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = LocalModelEngine(model_path=model_path)
    elif model_path and _engine_instance.model_path != model_path:
        print(f"[ENGINE] Switching active model to: {model_path.name}")
        _engine_instance = LocalModelEngine(model_path=model_path)
    return _engine_instance

def switch_model(model_path: Path) -> LocalModelEngine:
    global _engine_instance
    _engine_instance = LocalModelEngine(model_path=model_path)
    return _engine_instance
