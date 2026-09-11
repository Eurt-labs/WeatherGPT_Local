import os
from pathlib import Path
from typing import Generator, List, Dict, Any, Optional
from llama_cpp import Llama
from config import MODELS_DIR, N_CTX, N_THREADS, N_GPU_LAYERS, SECTOR_SYSTEM_PROMPTS, AVAILABLE_MODELS

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
        print(f"\n=======================================================")
        print(f"[ENGINE] Loading local GGUF model: {target_path.name}")
        print(f"[ENGINE] Size: {target_path.stat().st_size / (1024**3):.2f} GB")
        print(f"[ENGINE] Context: {N_CTX} tokens | CPU Threads: {N_THREADS} | GPU Layers: {N_GPU_LAYERS}")
        print(f"=======================================================\n")
        
        self.llm = Llama(
            model_path=str(target_path),
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False
        )
        print(f"[ENGINE] Model initialized and ready for offline inference!\n")

    def build_prompt_messages(
        self,
        user_message: str,
        location: str,
        weather_context: str,
        sector_focus: str,
        language: str,
        is_voice_mode: bool,
        history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        system_base = SECTOR_SYSTEM_PROMPTS.get(sector_focus.lower(), SECTOR_SYSTEM_PROMPTS["general"])
        
        system_prompt = (
            f"{system_base}\n\n"
            f"LIVE METEOROLOGICAL CONTEXT:\n"
            f"Location: {location}\n"
            f"{weather_context}\n"
        )

        if is_voice_mode:
            system_prompt += (
                "\nVOICE AI MODE ACTIVE: "
                "Give a natural, warm, conversational answer in 1 to 3 sentences maximum. "
                "Never use markdown formatting, asterisks, bullet points, or lists so speech synthesis sounds completely fluent."
            )
        else:
            system_prompt += (
                "\nCHAT MODE: "
                "Provide a clear, helpful, well-structured response with key weather insights."
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
            history=history or []
        )

        max_tokens = 256 if is_voice_mode else 768
        temperature = 0.6 if is_voice_mode else 0.7

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
        history: List[Dict[str, str]] = None
    ) -> str:
        tokens = list(self.stream_completion(
            user_message=user_message,
            location=location,
            weather_context=weather_context,
            sector_focus=sector_focus,
            language=language,
            is_voice_mode=is_voice_mode,
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
