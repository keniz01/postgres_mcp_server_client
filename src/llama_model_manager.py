import atexit
from llama_cpp import Llama, LLAMA_POOLING_TYPE_NONE

class LlamaModelManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Llama(
                model_path='./Phi-3.5-mini-instruct-Q6_K_L.gguf',
                verbose=False,
                temperature=0,
                pooling_type=LLAMA_POOLING_TYPE_NONE,
                n_ctx=2048
            )
            atexit.register(cls._cleanup)
        return cls._instance

    @classmethod
    def _cleanup(cls):
        if cls._instance is not None:
            try:
                cls._instance.close()  # ✅ Use the actual method provided by llama-cpp-python
            except Exception as e:
                print(f"Warning: Failed to close Llama model cleanly: {e}")
            finally:
                cls._instance = None
