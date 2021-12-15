# import flask related
from flask import Flask, request, abort, url_for
from urllib.parse import parse_qsl, parse_qs
from linebot.models import events, messages
from line_chatbot_api import *
from array import array
import os, time
from PIL import Image
import sys
import time
from keras.models import load_model
from PIL import Image, ImageOps
import numpy as np

# Load the model
model = load_model('keras_model.h5')

# create flask server
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500
    
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

@handler.add(MessageEvent)
def handle_something(event):
    if event.message.type=='text':
        recrive_text=event.message.text
        print(recrive_text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = '傳圖片給我，我會分辨剪刀、石頭、布'))
    elif event.message.type=='image':
        message_content = line_bot_api.get_message_content(event.message.id)
        with open('.\\static\\temp_image.png', 'wb') as fd:
            for chunk in message_content.iter_content():
                fd.write(chunk)

        # Create the array of the right shape to feed into the keras model
        # The 'length' or number of images you can put into the array is
        # determined by the first position in the shape tuple, in this case 1.
        data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
        # Replace this with the path to your image
        image = Image.open('.\\static\\temp_image.png')
        #resize the image to a 224x224 with the same strategy as in TM2:
        #resizing the image to be at least 224x224 and then cropping from the center
        size = (224, 224)
        image = ImageOps.fit(image, size, Image.ANTIALIAS)

        #turn the image into a numpy array
        image_array = np.asarray(image)
        # Normalize the image
        normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
        # Load the image into the array
        data[0] = normalized_image_array

        # run the inference
        prediction = model.predict(data)
        results=('剪刀', '石頭', '布', '未出拳')
        numerical_result=prediction.argmax()
        string_reply=f'你出的是{results[numerical_result]}' if 0<=numerical_result<2 else '你沒有出拳唷 ^^'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = string_reply))

# run app
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)