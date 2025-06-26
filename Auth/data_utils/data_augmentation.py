import tensorflow as tf
import random
import os
import cv2
import numpy as np
from tqdm import tqdm

def data_aug(img):
    """
    Apply multiple augmentations to an image
    
    Args:
        img: Input image tensor
        
    Returns:
        List of augmented images
    """
    data = []
    for i in range(9):
        img = tf.image.stateless_random_brightness(img, max_delta=0.02, seed=(1,2))
        img = tf.image.stateless_random_contrast(img, lower=0.6, upper=1, seed=(1,3))
        img = tf.image.stateless_random_flip_left_right(img, seed=(np.random.randint(100),np.random.randint(100)))
        img = tf.image.stateless_random_jpeg_quality(img, min_jpeg_quality=90, max_jpeg_quality=100, seed=(np.random.randint(100),np.random.randint(100)))
        img = tf.image.stateless_random_saturation(img, lower=0.9,upper=1, seed=(np.random.randint(100),np.random.randint(100)))
            
        data.append(img)
    
    return data

def augment_and_save_image(image_path, output_dir, num_augmentations=9):
    """
    Augment an image and save multiple versions
    
    Args:
        image_path: Path to the original image
        output_dir: Directory to save augmented images
        num_augmentations: Number of augmented versions to create
    """
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not read image: {image_path}")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get original filename without extension
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    # Save the original image first
    original_path = os.path.join(output_dir, f"{base_name}_original.jpg")
    cv2.imwrite(original_path, image)

    
    # Convert to tensorflow tensor for augmentation
    image_tensor = tf.convert_to_tensor(image)
    image_tensor = tf.cast(image_tensor, tf.float32) / 255.0
    
    # Apply augmentations
    augmented_images = data_aug(image_tensor)
    
    # Save augmented images
    for i, aug_img in enumerate(augmented_images):
        # Convert back to uint8
        aug_img = tf.cast(aug_img * 255, tf.uint8)
        aug_img = aug_img.numpy()
        
        # Save augmented image
        output_path = os.path.join(output_dir, f"{base_name}_aug_{i+1}.jpg")
        cv2.imwrite(output_path, cv2.cvtColor(aug_img, cv2.COLOR_RGB2BGR))

def augment_dataset(input_dir, output_dir, num_augmentations=9):
    """
    Augment all images in a dataset directory
    
    Args:
        input_dir: Directory containing original images
        output_dir: Directory to save augmented images
        num_augmentations: Number of augmented versions to create per image
    """
    print(f"\nAugmenting dataset from: {input_dir}")
    print(f"Saving to: {output_dir}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each person's directory
    for person_dir in tqdm(os.listdir(input_dir), desc="Processing people"):
        person_path = os.path.join(input_dir, person_dir)
        if not os.path.isdir(person_path):
            continue
            
        # Create person directory in output
        person_output_dir = os.path.join(output_dir, person_dir)
        os.makedirs(person_output_dir, exist_ok=True)
        
        # Process each image
        for img_name in os.listdir(person_path):
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            img_path = os.path.join(person_path, img_name)
            augment_and_save_image(img_path, person_output_dir, num_augmentations)
    
    print("\nDataset augmentation completed!")

if __name__ == "__main__":
    # Example usage
    input_dir = "Data/LFW"
    output_dir = "Data/LFW_augmented"
    augment_dataset(input_dir, output_dir, num_augmentations=9) 