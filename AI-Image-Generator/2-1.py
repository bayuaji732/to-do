import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

small_model = "Manojb/stable-diffusion-2-1-base"

pipe = StableDiffusionPipeline.from_pretrained(small_model, torch_dtype=torch.float16)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_attention_slicing()
pipe = pipe.to("cuda")

prompts = ["a cute kitten is wearing a plastic mask"]

results = pipe(
    prompts,
    num_inference_steps=20,
    guidance_scale=3.5,
    height=512,
    width=512
)

images = results.images

# Save or display the images
for i, img in enumerate(images):
    img.save(f"image_{i}.png")  # Save each image
