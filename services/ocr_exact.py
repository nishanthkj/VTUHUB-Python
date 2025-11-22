from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-stage1")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-stage1")

img = Image.open("../captcha.jpg").convert("RGB")

pixel_values = processor(images=img, return_tensors="pt").pixel_values
output_ids = model.generate(pixel_values, max_length=10)

text = processor.batch_decode(output_ids, skip_special_tokens=True)[0]
print(text)
