import os
import shutil
import argparse
import json
from tqdm import tqdm

from PIL import Image, ImageOps

# Initialize the arg parser
parser = argparse.ArgumentParser(description='Prepare the dataset to be uploaded to the 🤗')

parser.add_argument('--root_dir', type=str, help='The directory path to the original dataset')
parser.add_argument('--resolution', type=int, help='The final resolution of the processed images')

args = parser.parse_args()

ROOT_DIR = args.root_dir
RESOLUTION = args.resolution


FLAWLESS_KEYWORD    = 'flawless'
DISTORTED_KEYWORD   = 'distorted'
MASK_KEYWORD        = 'mask'
REFERENCE_KEYWORD   = 'reference'

PROMPT = "high quality, detailed, professional photograph of a woman standing"


# make the required directories
if not os.path.exists(FLAWLESS_KEYWORD):
    os.makedirs(FLAWLESS_KEYWORD)

if not os.path.exists(DISTORTED_KEYWORD):
    os.makedirs(DISTORTED_KEYWORD)

if not os.path.exists(MASK_KEYWORD):
    os.makedirs(MASK_KEYWORD)

if not os.path.exists(REFERENCE_KEYWORD):
    os.makedirs(REFERENCE_KEYWORD)


# Methods to resize the image with padding
def resize_with_padding(img, color='white'):
    expected_size = max(img.width, img.height)

    bordered_image = Image.new(
        "RGB", 
        (expected_size, expected_size), 
        (255, 255, 255) if color == 'white' else (0, 0, 0)
    )
    
    width_offset = (expected_size - img.width) // 2
    height_offset = (expected_size - img.height) // 2
    
    bordered_image.paste(img, (width_offset, height_offset))

    return bordered_image.resize((RESOLUTION, RESOLUTION))


# Copy the files into their corresponding directory
counter = 0
for subdir, dirs, files in tqdm(os.walk(ROOT_DIR)):
    reference_files = []
    mask_file = None
    distorted_file = None
    flawless_file = None
    for file in files:
        if file.startswith(REFERENCE_KEYWORD):
            reference_files.append(file)
        elif file.startswith(MASK_KEYWORD):
            mask_file = file
        elif file.startswith(DISTORTED_KEYWORD):
            distorted_file = file
        elif file.startswith(FLAWLESS_KEYWORD):
            flawless_file = file

    if len(reference_files) == 0 or mask_file == None or distorted_file == None or flawless_file == None:
        continue

    for reference_file in reference_files:
        reference_image = Image.open(os.path.join(subdir, reference_file))
        reference_image = resize_with_padding(reference_image)
        reference_image.save(os.path.join(REFERENCE_KEYWORD, f'{counter}.jpg'))

        mask_image = Image.open(os.path.join(subdir, mask_file))
        mask_image = resize_with_padding(mask_image, 'black')
        mask_image.save(os.path.join(MASK_KEYWORD, f'{counter}.jpg'))

        distorted_image = Image.open(os.path.join(subdir, distorted_file))
        distorted_image = resize_with_padding(distorted_image)
        distorted_image.save(os.path.join(DISTORTED_KEYWORD, f'{counter}.jpg'))

        flawless_image = Image.open(os.path.join(subdir, flawless_file))
        flawless_image = resize_with_padding(flawless_image)
        flawless_image.save(os.path.join(FLAWLESS_KEYWORD, f'{counter}.jpg'))
        
        counter += 1

print(f"Finished processing the dataset. Total number of samples: {counter}")


# Zip the directories
shutil.make_archive(FLAWLESS_KEYWORD, 'zip', './', FLAWLESS_KEYWORD)
shutil.make_archive(DISTORTED_KEYWORD, 'zip', './', DISTORTED_KEYWORD)
shutil.make_archive(MASK_KEYWORD, 'zip', './', MASK_KEYWORD)
shutil.make_archive(REFERENCE_KEYWORD, 'zip', './', REFERENCE_KEYWORD)

print("Archived all the directories!")


# Prepare the train.jsonl file
conf = open("train.jsonl","a")

for i in range(counter):
    line = json.dumps({
        "prompt": PROMPT,
        FLAWLESS_KEYWORD: f"{FLAWLESS_KEYWORD}/{i}.jpg",
        DISTORTED_KEYWORD: f"{DISTORTED_KEYWORD}/{i}.jpg",
        MASK_KEYWORD: f"{MASK_KEYWORD}/{i}.jpg",
        REFERENCE_KEYWORD: f"{REFERENCE_KEYWORD}/{i}.jpg",
    })
    conf.write(f"{line}\n")

conf.close()

print("Generated the train.jsonl file!")
