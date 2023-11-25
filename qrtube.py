import json
import os
import sys
from multiprocessing import Pool, cpu_count, Manager

import qrcode
from PIL import Image
from moviepy.editor import ImageSequenceClip


def create_directory(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def generate_frame(args):
    (
        frame_data,
        output_dir,
        frame_number,
        img_width,
        img_height,
        qr_box_size,
        qr_border,
        qr_size,
        num_horizontal,
        num_vertical,
    ) = args
    final_img = Image.new("RGB", (img_width, img_height), "white")

    for i, data_chunk in enumerate(frame_data):
        qr = qrcode.QRCode(
            version=40,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=qr_box_size,
            border=qr_border,
        )
        qr.add_data(data_chunk)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        x = (i % num_horizontal) * qr_size
        y = (i // num_horizontal) * qr_size

        final_img.paste(qr_img, (x, y))

    frame_filename = os.path.join(output_dir, f"frame_{frame_number}.png")
    final_img.save(frame_filename, format="PNG", optimize=True, compression_level=9)
    return frame_filename


def update_progress(result, progress, total_frames):
    progress.append(result)
    completed = len(progress)
    percentage = (completed / total_frames) * 100
    print(f"Progress: {percentage:.2f}% ({completed}/{total_frames} frames)")


def generate_frames(file_path, output_dir):
    img_width, img_height = 3840, 2160
    max_capacity = 1273
    qr_box_size = 4
    qr_border = 1
    qr_size = 177 * qr_box_size + 2 * qr_border

    num_horizontal = img_width // qr_size
    num_vertical = img_height // qr_size
    qr_codes_per_frame = num_horizontal * num_vertical

    total_file_size = os.path.getsize(file_path)
    total_qr_codes = (total_file_size + max_capacity - 1) // max_capacity
    total_frames = (total_qr_codes + qr_codes_per_frame - 1) // qr_codes_per_frame

    metadata = {
        "file_name": os.path.basename(file_path),
        "file_size": total_file_size,
        "total_qr_codes": total_qr_codes,
        "total_frames": total_frames,
    }
    metadata_json = json.dumps(metadata)

    with open(file_path, "rb") as file:
        file_chunks = [metadata_json] + [
            file.read(max_capacity) for _ in range(total_qr_codes)
        ]

    # Organize data into frames
    frame_data = [
        file_chunks[i : i + qr_codes_per_frame]
        for i in range(0, len(file_chunks), qr_codes_per_frame)
    ]

    manager = Manager()
    progress = manager.list()

    pool = Pool(cpu_count())
    for frame_number, data in enumerate(frame_data):
        args = (
            data,
            output_dir,
            frame_number,
            img_width,
            img_height,
            qr_box_size,
            qr_border,
            qr_size,
            num_horizontal,
            num_vertical,
        )
        pool.apply_async(
            generate_frame,
            args=(args,),
            callback=lambda result: update_progress(result, progress, total_frames),
        )

    pool.close()
    pool.join()

    return list(progress)


# ffmpeg -r 60 -i frame_%d.png -c:v libx265 -crf 38 -threads auto out.mp4
# ffmpeg -r 60 -i frame_%d.png -c:v h264_nvenc out.mp4
# ffmpeg -y -vsync 0 -c:v h264_cuvid -i input.mp4 output.yuv
def create_video(frame_filenames, output_dir, fps=60):
    clip = ImageSequenceClip(frame_filenames, fps=fps)
    video_file = os.path.join(output_dir, "output_video.mp4")
    # clip.write_videofile(video_file, codec="libx264")
    clip.write_videofile(video_file, codec="h264_nvenc")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    output_dir = f"{os.path.splitext(file_path)[0]}_frames"
    create_directory(output_dir)

    frame_filenames = generate_frames(file_path, output_dir)
    # create_video(frame_filenames, output_dir)
    # print("Video creation completed.")
