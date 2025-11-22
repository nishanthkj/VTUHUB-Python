import easyocr
reader = easyocr.Reader(['en'])

result = reader.readtext('captcha.jpg', detail=0)
print("".join(result))
