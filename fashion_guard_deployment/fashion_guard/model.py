import importlib
from typing import Any

from .prompts import SYSTEM_PROMPT, build_user_prompt


class QwenGuardModel:
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-4B-Instruct-2507",
        model: Any = None,
        tokenizer: Any = None,
        accelerator: str = "auto",
        quantization: str = "none",
    ):
        if accelerator not in {"auto", "cuda", "tpu", "cpu"}:
            raise ValueError("accelerator must be one of: auto, cuda, tpu, cpu")
        if quantization not in {"none", "8bit", "4bit"}:
            raise ValueError("quantization must be one of: none, 8bit, 4bit")
        self.model_name = model_name
        self.model = model
        self.tokenizer = tokenizer
        self.accelerator = accelerator
        self.quantization = quantization
        self.active_accelerator: str | None = None
        self.device = None
        self._xla_model = None

    def _ensure_quantization_supported(self, active_accelerator: str) -> None:
        # bitsandbytes only implements CUDA kernels; larger models on TPU/CPU
        # must be tried unquantized or not at all.
        if self.quantization != "none" and active_accelerator != "cuda":
            raise RuntimeError("quantization requires the cuda accelerator")

    def _load_kwargs(self) -> dict[str, bool]:
        # transformers>=4.53 ships native Phi3/Phi4 support, so remote code is never needed
        # and we avoid depending on a Hub revision's code matching the installed API.
        return {}

    def _resolve_runtime(self):
        torch = importlib.import_module("torch")
        if self.accelerator in {"auto", "cuda"} and torch.cuda.is_available():
            return "cuda", torch.device("cuda"), torch, None
        if self.accelerator in {"auto", "tpu"}:
            try:
                xla_model = importlib.import_module("torch_xla.core.xla_model")
                return "tpu", xla_model.xla_device(), torch, xla_model
            except ModuleNotFoundError:
                if self.accelerator == "tpu":
                    raise RuntimeError("TPU mode requires torch_xla in the active environment") from None
        if self.accelerator == "cuda":
            raise RuntimeError("CUDA mode requested but no CUDA device is available")
        return "cpu", torch.device("cpu"), torch, None

    def _load(self) -> None:
        if self.model is not None and self.tokenizer is not None:
            return
        transformers = importlib.import_module("transformers")
        active_accelerator, device, torch, xla_model = self._resolve_runtime()
        self._ensure_quantization_supported(active_accelerator)
        load_kwargs = self._load_kwargs()
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(self.model_name, **load_kwargs)
        if active_accelerator == "tpu":
            self.model = transformers.AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16,
                attn_implementation="eager",
                **load_kwargs,
            ).to(device)
        else:
            model_kwargs = dict(load_kwargs)
            if self.quantization == "4bit":
                model_kwargs["quantization_config"] = transformers.BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                )
            elif self.quantization == "8bit":
                model_kwargs["quantization_config"] = transformers.BitsAndBytesConfig(load_in_8bit=True)
            else:
                model_kwargs["torch_dtype"] = "auto"
            if active_accelerator == "cuda":
                model_kwargs["device_map"] = "auto"
            self.model = transformers.AutoModelForCausalLM.from_pretrained(self.model_name, **model_kwargs)
        self.model.eval()
        self.active_accelerator = active_accelerator
        self.device = device
        self._xla_model = xla_model

    def _chat_template_kwargs(self) -> dict[str, bool]:
        if self.model_name.startswith("Qwen/Qwen3-"):
            return {"enable_thinking": False}
        return {}

    def generate(self, query: str, context: list[str] | None = None, max_new_tokens: int = 20) -> str:
        self._load()
        torch = importlib.import_module("torch")
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": build_user_prompt(query, context)}]
        # Render to plain text first and tokenize separately: some chat templates
        # (e.g. Qwen3-30B-A3B) make apply_chat_template(tokenize=True, return_dict=True)
        # raise inside the fast tokenizer's batch encoder.
        prompt_text = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False,
            **self._chat_template_kwargs(),
        )
        # Terminal/paste input can contain invalid surrogate code points that the
        # Rust tokenizers binding rejects with a confusing union-type TypeError.
        prompt_text = prompt_text.encode("utf-8", "replace").decode("utf-8")
        inputs = self.tokenizer(prompt_text, return_tensors="pt").to(self.device or self.model.device)
        # torch.inference_mode() marks tensors in a way that conflicts with
        # torch_xla's lazy tensor tracing (RuntimeError: "Cannot set
        # version_counter for inference tensor" inside rotary embeddings on
        # TPU); torch.no_grad() avoids that while still skipping autograd.
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
        if self._xla_model is not None:
            self._xla_model.mark_step()
        generated = outputs[0, inputs["input_ids"].shape[-1]:]
        return self.tokenizer.decode(generated.detach().cpu().tolist(), skip_special_tokens=True)
