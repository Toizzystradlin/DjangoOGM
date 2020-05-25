import qrcode
import os
import shutil
import PIL
from PIL import Image
def create_qr(eq_id):
    num = str(eq_id)
    value = 'http://t.me/Ogmtestbot?start=' + num
    img = qrcode.make(value)
    img.save(num + '.png')
    shutil.move(num + '.png', 'main/static/images/qr_codes/' + num + '.png')



