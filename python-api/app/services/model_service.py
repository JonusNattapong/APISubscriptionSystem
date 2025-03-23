import os
import logging
from typing import Dict, Any, List, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Pipeline
from diffusers import StableDiffusionPipeline
import onnxruntime as ort
from app.core.config import settings

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self):
        self.model_dir = settings.MODEL_DIR
        self.loaded_models: Dict[str, Any] = {}
        self.available_models: Dict[str, Dict[str, Any]] = {}
        self.scan_models()
    
    def scan_models(self) -> None:
        """Scan the model directory for available models"""
        logger.info(f"Scanning models in {self.model_dir}")
        
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir, exist_ok=True)
            logger.info(f"Created model directory at {self.model_dir}")
            return
        
        # Scan for different model types
        for root, dirs, files in os.walk(self.model_dir):
            # Check for transformers models (look for config.json)
            if "config.json" in files:
                model_path = root
                model_name = os.path.basename(root)
                self.available_models[model_name] = {
                    "path": model_path,
                    "type": "transformers",
                    "loaded": False
                }
                logger.info(f"Found transformers model: {model_name} at {model_path}")
            
            # Check for ONNX models
            for file in files:
                if file.endswith(".onnx"):
                    model_path = os.path.join(root, file)
                    model_name = os.path.splitext(file)[0]
                    self.available_models[model_name] = {
                        "path": model_path,
                        "type": "onnx",
                        "loaded": False
                    }
                    logger.info(f"Found ONNX model: {model_name} at {model_path}")
            
            # Check for stable diffusion models
            if "model_index.json" in files:
                model_path = root
                model_name = os.path.basename(root)
                self.available_models[model_name] = {
                    "path": model_path,
                    "type": "stable-diffusion",
                    "loaded": False
                }
                logger.info(f"Found Stable Diffusion model: {model_name} at {model_path}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get a list of all available models"""
        return [
            {
                "name": name,
                "type": info["type"],
                "loaded": info["loaded"]
            }
            for name, info in self.available_models.items()
        ]
    
    def load_model(self, model_name: str) -> bool:
        """Load a model into memory"""
        if model_name not in self.available_models:
            logger.error(f"Model {model_name} not found")
            return False
        
        if self.available_models[model_name]["loaded"]:
            logger.info(f"Model {model_name} already loaded")
            return True
        
        model_info = self.available_models[model_name]
        model_path = model_info["path"]
        model_type = model_info["type"]
        
        try:
            if model_type == "transformers":
                # Load text generation model
                model = AutoModelForCausalLM.from_pretrained(model_path)
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.loaded_models[model_name] = {
                    "model": model,
                    "tokenizer": tokenizer
                }
                
            elif model_type == "onnx":
                # Load ONNX model
                session = ort.InferenceSession(model_path)
                self.loaded_models[model_name] = {
                    "session": session
                }
                
            elif model_type == "stable-diffusion":
                # Load Stable Diffusion model
                pipeline = StableDiffusionPipeline.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16
                )
                pipeline.to("cuda" if torch.cuda.is_available() else "cpu")
                self.loaded_models[model_name] = {
                    "pipeline": pipeline
                }
            
            self.available_models[model_name]["loaded"] = True
            logger.info(f"Successfully loaded model {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return False
    
    def unload_model(self, model_name: str) -> bool:
        """Unload a model from memory"""
        if model_name not in self.loaded_models:
            logger.error(f"Model {model_name} not loaded")
            return False
        
        try:
            # Remove model from loaded models
            del self.loaded_models[model_name]
            self.available_models[model_name]["loaded"] = False
            
            # Force garbage collection to free up memory
            import gc
            gc.collect()
            torch.cuda.empty_cache()
            
            logger.info(f"Successfully unloaded model {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload model {model_name}: {e}")
            return False
    
    def generate_text(self, model_name: str, prompt: str, max_tokens: int = 100) -> Optional[str]:
        """Generate text using a loaded model"""
        if model_name not in self.loaded_models:
            if not self.load_model(model_name):
                return None
        
        model_info = self.available_models[model_name]
        if model_info["type"] != "transformers":
            logger.error(f"Model {model_name} is not a text generation model")
            return None
        
        try:
            model_data = self.loaded_models[model_name]
            model = model_data["model"]
            tokenizer = model_data["tokenizer"]
            
            inputs = tokenizer(prompt, return_tensors="pt")
            
            # Move to GPU if available
            if torch.cuda.is_available():
                model = model.cuda()
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            outputs = model.generate(
                **inputs,
                max_length=max_tokens,
                num_return_sequences=1,
                pad_token_id=tokenizer.eos_token_id
            )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
            
        except Exception as e:
            logger.error(f"Text generation failed with model {model_name}: {e}")
            return None
    
    def generate_image(self, model_name: str, prompt: str) -> Optional[bytes]:
        """Generate an image using a Stable Diffusion model"""
        if model_name not in self.loaded_models:
            if not self.load_model(model_name):
                return None
        
        model_info = self.available_models[model_name]
        if model_info["type"] != "stable-diffusion":
            logger.error(f"Model {model_name} is not an image generation model")
            return None
        
        try:
            pipeline = self.loaded_models[model_name]["pipeline"]
            
            # Generate image
            with torch.no_grad():
                image = pipeline(prompt).images[0]
            
            # Convert to bytes
            import io
            from PIL import Image
            
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
            
            return image_bytes
            
        except Exception as e:
            logger.error(f"Image generation failed with model {model_name}: {e}")
            return None
    
    def run_onnx_model(self, model_name: str, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run inference with an ONNX model"""
        if model_name not in self.loaded_models:
            if not self.load_model(model_name):
                return None
        
        model_info = self.available_models[model_name]
        if model_info["type"] != "onnx":
            logger.error(f"Model {model_name} is not an ONNX model")
            return None
        
        try:
            session = self.loaded_models[model_name]["session"]
            
            # Get input names
            input_names = [input.name for input in session.get_inputs()]
            
            # Prepare inputs
            onnx_inputs = {}
            for name in input_names:
                if name in inputs:
                    onnx_inputs[name] = inputs[name]
                else:
                    logger.error(f"Required input {name} not provided")
                    return None
            
            # Run inference
            outputs = session.run(None, onnx_inputs)
            
            # Get output names
            output_names = [output.name for output in session.get_outputs()]
            
            # Prepare outputs
            result = {name: outputs[i] for i, name in enumerate(output_names)}
            return result
            
        except Exception as e:
            logger.error(f"ONNX inference failed with model {model_name}: {e}")
            return None

# Create a singleton instance
model_service = ModelService()
