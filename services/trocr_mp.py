"""
trocr_runner.py

Convert your script into a reusable class. All behaviour is configurable via
constructor args (defaults provided). You can pass a custom `clean_fn` or let
the class import `Gray.clean_captcha` by default.

Usage example:
    runner = TrOCRRunner(folder="captchas", enable_clean=True, model_name="microsoft/trocr-base-stage1")
    runner.process_all()                 # processes, prints colored output, writes results.csv
    # Or override defaults:
    runner = TrOCRRunner(folder="my_captchas", out_csv="out.csv", max_length=14, device="cpu")
    runner.process_all()
"""
from typing import Callable, Optional
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import os, csv, time
import torch

class TrOCRRunner:
    def __init__(
        self,
        folder: str = "captchas",
        model_name: str = "microsoft/trocr-base-stage1",
        hf_home: Optional[str] = None,
        enable_clean: bool = True,
        clean_fn: Optional[Callable[[Image.Image], Image.Image]] = None,
        out_csv: str = "results.csv",
        max_length: int = 10,
        device: Optional[str] = None,
        print_colors: bool = True,
    ):
        """
        Create a runner instance.

        Args:
            folder: directory with images (filenames' stem = expected text).
            model_name: HuggingFace TrOCR model id.
            hf_home: path to set HF_HOME (optional).
            enable_clean: call clean_fn on images if True.
            clean_fn: callable(Image) -> Image; if None the runner will try to import Gray.clean_captcha.
            out_csv: path to write results CSV.
            max_length: generation max length for model.generate.
            device: 'cuda' / 'cpu' / None (auto). If you want a specific GPU use 'cuda:0'.
            print_colors: whether to color console output (ANSI).
        """
        if hf_home:
            os.environ["HF_HOME"] = str(hf_home)
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

        self.folder = folder
        self.model_name = model_name
        self.enable_clean = enable_clean
        self.out_csv = out_csv
        self.max_length = max_length
        self.print_colors = print_colors

        # choose device
        if device:
            self.device = torch.device(device if torch.cuda.is_available() or "cpu" in device else "cpu")
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # load cleaning function or default
        if clean_fn:
            self.clean_fn = clean_fn
        else:
            # lazy import so module is optional
            try:
                from Gray import clean_captcha
                self.clean_fn = clean_captcha
            except Exception:
                # fallback identity function
                self.clean_fn = lambda im: im

        # load model + processor once
        self.processor = TrOCRProcessor.from_pretrained(self.model_name,use_fast=True)
        self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name).to(self.device)
        self.model.eval()

        # ANSI colors
        self.GREEN = "\033[92m" if self.print_colors else ""
        self.RED = "\033[91m" if self.print_colors else ""
        self.RESET = "\033[0m" if self.print_colors else ""

    def _ensure_rgb_pil(self, img):
        """Convert numpy or grayscale to RGB PIL Image."""
        from PIL import Image as PILImage
        if not isinstance(img, PILImage.Image):
            img = PILImage.fromarray(img)
        if img.mode != "RGB":
            img = img.convert("RGB")
        return img

    def run_ocr(self, img) -> str:
        """
        Run TrOCR on a PIL Image (or numpy array). Returns cleaned single-string result.
        """
        start = time.time()
        # apply cleaning if enabled
        if self.enable_clean:
            img_clean = self.clean_fn(img)
        else:
            img_clean = img

        img_clean = self._ensure_rgb_pil(img_clean)

        inputs = self.processor(images=img_clean, return_tensors="pt")
        pixel_values = inputs.pixel_values.to(self.device)
        with torch.no_grad():
            out_ids = self.model.generate(pixel_values, max_length=self.max_length)
        text = self.processor.batch_decode(out_ids, skip_special_tokens=True)[0]
        # postprocess: remove periods, collapse whitespace
        text = text.replace(".", "")
        text = "".join(text.split())
        # timing print (optional)
        elapsed = time.time() - start
        print(f"Time: {elapsed:.2f}s", end=" ")
        return text

    def process_file(self, path: str) -> list:
        """
        Process one file path. Returns a row [file, expected, ocr_raw, ocr_clean, match].
        """
        name = os.path.basename(path)
        expected = os.path.splitext(name)[0]
        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            # image read failed -> record as error
            row = [name, expected, "", "", 0]
            print(f"{self.RED}ERR{self.RESET}: cannot open {name}: {e}")
            return row
        SYMBOL_MAP = str.maketrans({
            '£': 'F',
            '@': 'A',
            '$': 'S',
            '!': 'I',
            '|': 'I',
            '§': 'S',
            '€': 'E',
            '¥': 'Y',
            '¢': 'C',
            '?': '',
            '*': '',
            '#': '',
            ',': '',
            '.': '',
            ':': '',
            "'": '',
        })

        ocr_raw = self.run_ocr(img)
        ocr_clean = "".join(ocr_raw.split())
        ocr_clean = ocr_clean.translate(SYMBOL_MAP)
        match = int(ocr_clean == expected)

        if match:
            print(f"{self.GREEN}MATCH{self.RESET}: {ocr_clean} == {expected} ({name})")
        else:
            print(f"{self.RED}MISMATCH{self.RESET}: {ocr_clean} != {expected} ({name})")

        return [name, expected, ocr_raw, ocr_clean, match]

    def process_all(self, write_csv: bool = True) -> list:
        """
        Process all images and write CSV incrementally so it's always updated.
        Returns list of rows.
        """
        rows = []
        if not os.path.isdir(self.folder):
            raise FileNotFoundError(f"Folder not found: {self.folder}")

        files = sorted(
            [os.path.join(self.folder, f) for f in os.listdir(self.folder)
             if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        )

        csv_path = os.path.abspath(self.out_csv)
        print("Working dir:", os.path.abspath(os.getcwd()))
        print("CSV path:", csv_path)

        f = None
        try:
            if write_csv:
                f = open(csv_path, "w", newline="", encoding="utf-8")
                w = csv.writer(f)
                w.writerow(["file", "expected", "ocr", "clean", "match"])
                f.flush()
                os.fsync(f.fileno())
            else:
                w = None

            for p in files:
                try:
                    row = self.process_file(p)
                except Exception as e:
                    # record the error row to CSV so nothing is lost
                    name = os.path.basename(p)
                    expected = os.path.splitext(name)[0]
                    row = [name, expected, "", f"ERROR: {e}", 0]
                    print(f"{self.RED}ERR{self.RESET}: processing {name}: {e}")

                rows.append(row)

                if write_csv:
                    w.writerow(row)
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except Exception:
                        # fsync may fail on some platforms/permissions; ignore but print
                        print("Warning: fsync failed (permission or platform).")
        finally:
            if f:
                f.close()

        print("Done. Wrote", len(rows), "rows to", csv_path)
        return rows


# ------------------ Example usage (default behaviour) ------------------
if __name__ == "__main__":
    # Default: uses Gray.clean_captcha if available, folder "captchas"
    runner = TrOCRRunner(folder="captchas",
                         #model_name="microsoft/trocr-base-printed"
                         )
    runner.process_all()
