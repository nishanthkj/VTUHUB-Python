from PIL import Image, ImageOps, ImageFilter
import numpy as np

def clean_captcha(img):
    # img = Image.open(input_path)

    # 1) convert to grayscale
    gray = ImageOps.grayscale(img)

    # 2) mild median filter to remove tiny speckles
    gray = gray.filter(ImageFilter.MedianFilter(size=3))

    arr = np.array(gray).astype(np.uint8)

    # 3) adaptive-ish threshold
    threshold = (arr.mean() + arr.min()) / 2
    binary = (arr < threshold).astype(np.uint8) * 255

    # 4) mask: 1 for foreground
    mask = (binary == 255).astype(np.uint8)

    # 5) majority filter (3×3)
    pad = np.pad(mask, 1, mode='constant', constant_values=0)
    h, w = mask.shape
    out_mask = np.zeros_like(mask)

    for i in range(h):
        for j in range(w):
            window = pad[i:i+3, j:j+3]
            out_mask[i, j] = 1 if window.sum() >= 5 else 0

    # 6) final image: black text (0), white background (255)
    result_arr = np.where(out_mask == 1, 0, 255).astype(np.uint8)

    # RETURN PIL IMAGE (not save)
    return Image.fromarray(result_arr)


# your paths
if __name__ == "__main__":
    img = Image.open("captcha.jpg")       # load original image
    cleaned = clean_captcha(img)          # run function
    cleaned.save("captcha_clean_gray.jpg")

