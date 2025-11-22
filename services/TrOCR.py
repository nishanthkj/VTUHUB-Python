from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
from .Gray import clean_captcha
import time
import os
import csv
os.environ["HF_HOME"] = os.getcwd()
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"



# load ONCE
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-stage1")
                                           #,use_fast=True
                                           #)
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-stage1")

model.eval()

def run_ocr(img):
    start = time.time()
    ENABLE_CLEAN = True
    if ENABLE_CLEAN:
        cleaned = clean_captcha(img)
    else:
        cleaned = img

    # --- FIX: ensure RGB PIL image ---
    if not isinstance(cleaned, Image.Image):
        cleaned = Image.fromarray(cleaned)

    if cleaned.mode != "RGB":
        cleaned = cleaned.convert("RGB")
    # ----------------------------------

    #img = clean_captcha(Image.open("captcha.jpg").convert("RGB"))
    pixel_values = processor(images=cleaned, return_tensors="pt").pixel_values

    output_ids = model.generate(pixel_values, max_length=10)

    text = processor.batch_decode(output_ids, skip_special_tokens=True)[0]

    print("Time:", time.time() - start)
    ctext = text.replace(".", "")
    cap_text = "".join((ctext.split()))
    return cap_text

    return

if __name__ == "__main__":
    img = Image.open("../captcha.jpg").convert("RGB")
    text = run_ocr(img)
    print(text)

# if __name__ == "__main__":
#     FOLDER = "captchas"
#     GREEN = "\033[92m"
#     RED = "\033[91m"
#     RESET = "\033[0m"
#
#     with open("results.csv", "w", newline="", encoding="utf-8") as f:
#         w = csv.writer(f)
#         w.writerow(["file", "expected", "ocr", "clean", "match"])
#
#         for file in os.listdir(FOLDER):
#             if not file.lower().endswith((".jpg", ".jpeg", ".png")):
#                 continue
#
#             img = Image.open(os.path.join(FOLDER, file)).convert("RGB")
#             ocr = run_ocr(img)
#             clean = "".join(ocr.split()).replace(".", "")
#             exp = os.path.splitext(file)[0]
#             match = clean == exp
#
#             # write CSV
#             w.writerow([file, exp, ocr, clean, match])
#
#             # colored console output
#             if match:
#                 print(f"{GREEN}MATCH{RESET}: {clean} == {exp} ({file})")
#             else:
#                 print(f"{RED}MISMATCH{RESET}: {clean} != {exp} ({file})")