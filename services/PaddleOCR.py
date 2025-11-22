from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='en')
res = ocr.ocr('captcha.jpg', cls=True)

text = ""
for line in res:
    for part in line:
        text += part[1][0]  # recognized text
print(text)
