from PIL import Image

def analyze_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        return f"Image format: {img.format}, size: {img.size}, mode: {img.mode}"
    except Exception as e:
        return f"Error analyzing image: {e}"
