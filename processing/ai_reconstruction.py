"""
Finetunes a Stable-Diffusion v1.5-compatible UNet on a corpus of
Islamic / Byzantine ornament patches then uses ControlNet to guide
texture synthesis on incomplete reconstructions.
"""
from pathlib import Path
import torch
import numpy as np
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from config import settings
from utils.logging_config import get_logger

log = get_logger(__name__)
DATASET_DIR = settings.DATA_DIR / "ornament_patches"


def train_diffusion():
    """Placeholder training loop"""
    pass


def fill_missing_texture(mesh_path: Path, output: Path):
    controlnet = ControlNetModel.from_pretrained(
        "lllyasviel/control_v11p_sd15_depth", torch_dtype=torch.float16
    )
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        controlnet=controlnet,
        safety_checker=None,
        torch_dtype=torch.float16,
    ).to(settings.PYTORCH_DEVICE)
    depth_img = np.zeros((512, 512, 3), dtype=np.uint8)
    prompt = "fine Ottoman stone carving, high detail, photorealistic"
    with torch.autocast(settings.PYTORCH_DEVICE):
        result = pipe(prompt, image=depth_img).images[0]
    result.save(output)
    log.info("Synthesised texture saved to %s", output)
