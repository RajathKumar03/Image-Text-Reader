from flask import Flask, request, render_template, jsonify, url_for, send_from_directory
from PIL import Image, ImageDraw
import easyocr
import os
import threading
import cv2
from skimage import io

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

reader = easyocr.Reader(['en'], gpu=False, model_storage_directory='path_to_model_directory')


@app.route('/')
def index():
    return render_template('index.html')  # Ensure your HTML file is named index.html


@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        image = Image.open(file_path)

        image.thumbnail((800, 800), Image.LANCZOS)
        thread = threading.Thread(target=process_image, args=(image, file.filename))
        thread.start()

        return jsonify({
            'status': 'Processing started',
            'image_url': url_for('processed_file', filename=file.filename)
        })

    return jsonify({'error': 'File upload failed'})


def process_image(image, filename):


    bounds = reader.readtext(image)
    detected_text = [text[1] for text in bounds]

    image_with_boxes = draw_boxes(image, bounds)

    processed_image_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    image_with_boxes.save(processed_image_path)

    text_result_path = os.path.join(app.config['PROCESSED_FOLDER'], filename + '.txt')
    with open(text_result_path, 'w') as f:
        f.write('\n'.join(detected_text))
0

@app.route('/processed/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)


@app.route('/processed_text/<filename>')
def processed_text_file(filename):
    filename += '.txt'
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)


def draw_boxes(image, bounds, color='yellow', width=2):
    draw = ImageDraw.Draw(image)
    for bound in bounds:
        p0, p1, p2, p3 = bound[0]
        draw.polygon([*p0, *p1, *p2, *p3], outline=color, width=width)
    return image


if __name__ == '__main__':
    app.run(debug=True)
