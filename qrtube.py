import json
import sys

import qrcode
from PIL import Image


def main(file_path):
    # Image dimensions and QR code parameters
    img_width, img_height = 3840, 2160
    max_capacity = 1273  # bytes for each QR code with high error correction
    qr_box_size = 4  # Size of each box in pixels
    qr_border = 1  # Border size in boxes
    qr_size = 177 * qr_box_size + 2 * qr_border  # Total QR code size including border

    # Calculate how many QR codes fit horizontally and vertically
    num_horizontal = img_width // qr_size
    num_vertical = img_height // qr_size
    qr_codes_per_image = num_horizontal * num_vertical

    # Determine the total size of the file
    total_file_size = 0
    with open(file_path, "rb") as file:
        file.seek(0, 2)  # Move the cursor to the end of the file
        total_file_size = file.tell()

    # Calculate the total number of QR codes needed
    total_qr_codes = (total_file_size + max_capacity - 1) // max_capacity

    # Metadata for the first QR code
    metadata = {
        "file_name": file_path.split("/")[-1],
        "file_size": total_file_size,
        "total_qr_codes": total_qr_codes + 1,  # Including the metadata QR code
    }
    metadata_json = json.dumps(metadata)

    # Open the file again to read and process in chunks
    with open(file_path, "rb") as file:
        image_number = 0
        qr_code_index = 0  # Index of QR code in the current image
        processed_bytes = 0  # Total bytes processed so far

        while True:
            # Handle metadata QR code
            if image_number == 0 and qr_code_index == 0:
                data_chunk = metadata_json
            else:
                data_chunk = file.read(max_capacity)
                if not data_chunk:
                    break  # Break if no more data to read

            processed_bytes += len(data_chunk)
            progress_percentage = (processed_bytes / total_file_size) * 100

            # Create a new image if needed
            if qr_code_index % qr_codes_per_image == 0 and qr_code_index > 0:
                final_img.save(f"final_qr_grid_{image_number}.png")
                image_number += 1
                qr_code_index = 0  # Reset QR code index for new image
                print(f"Progress: {progress_percentage:.2f}%")

            if qr_code_index == 0:
                final_img = Image.new("RGB", (img_width, img_height), "white")

            # Generate QR code
            qr = qrcode.QRCode(
                version=40,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=qr_box_size,
                border=qr_border,
            )
            qr.add_data(data_chunk)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Calculate position relative to the current image
            x = (qr_code_index % num_horizontal) * qr_size
            y = (qr_code_index // num_horizontal) * qr_size

            # Place QR code on the final image
            final_img.paste(qr_img, (x, y))

            qr_code_index += 1

        # Save the last image if it has any QR codes
        if qr_code_index % qr_codes_per_image > 0:
            final_img.save(f"final_qr_grid_{image_number}.png")
            print(f"Progress: {progress_percentage:.2f}%")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <file_path>")
        sys.exit(1)

    main(sys.argv[1])
