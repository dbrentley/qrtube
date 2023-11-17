from PIL import Image
from pyzbar.pyzbar import decode


def decode_qr_code(file_path):
    image = Image.open(file_path)
    decoded_objects = decode(image)
    for obj in decoded_objects:
        print("Type:", obj.type)
        print("Data:", obj.data.decode("utf-8"))


# Replace 'path_to_qr_code_image' with the path to your QR code image
decode_qr_code("C:/Users/brent/PycharmProjects/qrtube/metadata.png")
