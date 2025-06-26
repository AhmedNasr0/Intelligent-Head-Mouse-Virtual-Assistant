import tensorflow as tf
import os
import random
from glob import glob
import numpy as np
import matplotlib.pyplot as plt

def preprocess(file_path):
    """Scale and resize image"""
    byte_img = tf.io.read_file(file_path)
    image = tf.io.decode_jpeg(byte_img)
    image = tf.image.resize(image, (105,105))
    image = image / 255.0
    return image

def get_image_pairs(dataset_path, num_samples=5000):
    """Generate positive and negative image pairs from a single dataset folder"""
    people_images = {}

    # Collect all images and group by person
    for img_path in glob(os.path.join(dataset_path,"*", "*.jpg")):
        # Extract person name from filename (assuming format: person_name_original.jpg or person_name_aug_N.jpg)
        base_name = os.path.basename(img_path)
        person_name = base_name.split('_')[0]  # Get person name from filename
        
        if person_name not in people_images:
            people_images[person_name] = []
        people_images[person_name].append(img_path)

    # Filter people with at least 2 images
    valid_people = {k: v for k, v in people_images.items() if len(v) >= 2}

    if not valid_people:
        raise ValueError("No people found with 2 or more images in the dataset")

    positive_pairs = []
    negative_pairs = []
    people = list(valid_people.keys())

    # Generate positive pairs
    for person in valid_people:
        images = valid_people[person]
        num_positive = min(num_samples // len(valid_people), len(images) * (len(images) - 1) // 2)

        for _ in range(num_positive):
            img1, img2 = random.sample(images, 2)
            positive_pairs.append((img1, img2, 1))

    # Generate negative pairs
    if len(people) < 2:
        raise ValueError("Need at least 2 different people in the dataset")

    num_negative = min(len(positive_pairs), num_samples)  # Balance positive and negative pairs

    for _ in range(num_negative):
        while True:
            p1, p2 = random.sample(people, 2)
            if p1 != p2:  # Ensure different people
                img1 = random.choice(valid_people[p1])
                img2 = random.choice(valid_people[p2])
                negative_pairs.append((img1, img2, 0))
                break

    print(f"\nDataset Summary:")
    print(f"Total people: {len(people)}")
    print(f"People with 2+ images: {len(valid_people)}")
    print(f"Positive pairs generated: {len(positive_pairs)}")
    print(f"Negative pairs generated: {len(negative_pairs)}")

    return positive_pairs, negative_pairs

def get_training_data(dataset_path):
    """Prepare training and testing datasets from a single dataset folder"""
    if not os.path.exists(dataset_path):
        raise ValueError(f"Dataset path does not exist: {dataset_path}")

    print(f"Loading dataset from: {dataset_path}")

    positive_pairs, negative_pairs = get_image_pairs(dataset_path)
    data = positive_pairs + negative_pairs
    random.shuffle(data)

    if not data:
        raise ValueError("No valid image pairs found in the dataset")

    file_paths_1, file_paths_2, labels = zip(*data)

    # Create separate datasets for each component
    anchor = tf.data.Dataset.from_tensor_slices(list(file_paths_1))
    compare = tf.data.Dataset.from_tensor_slices(list(file_paths_2))
    labels_ds = tf.data.Dataset.from_tensor_slices(list(labels))

    # Create the combined dataset with the same structure as data_preprocessing.py
    dataset = tf.data.Dataset.zip((anchor, compare, labels_ds))

    # Map preprocessing function
    dataset = dataset.map(preprocess_twin)

    # Cache and shuffle
    dataset = dataset.cache()
    dataset = dataset.shuffle(buffer_size=10000)

    batch_size = 16
    # Split into training and testing
    total_data = len(data)
    train_size = int(total_data * 0.7)
    test_size = total_data - train_size

    train_data = dataset.take(train_size)
    train_data = train_data.batch(batch_size)
    train_data = train_data.prefetch(8)

    test_data = dataset.skip(train_size)
    test_data = test_data.take(test_size)
    test_data = test_data.batch(batch_size)
    test_data = test_data.prefetch(8)

    print(f"\nDataset prepared:")
    print(f"Total pairs: {total_data}")
    print(f"Training pairs: {train_size}")
    print(f"Testing pairs: {test_size}")
    print(f"Batch size: {batch_size}")

    return train_data, test_data

def preprocess_twin(input_img, validation_img, label):
    """Preprocess image pairs"""
    return (preprocess(input_img), preprocess(validation_img), label)

def visualize_batch(batch, num_pairs=5):
    """
    Visualize pairs of images from a batch
    Args:
        batch: Batch of data containing (anchor_images, positive/negative_images, labels)
        num_pairs: Number of pairs to display
    """
    # Unpack the batch - now matches data_preprocessing.py structure
    anchor_images, compare_images, labels = batch

    # Convert to numpy for visualization
    anchor_images = anchor_images.numpy()
    compare_images = compare_images.numpy()
    labels = labels.numpy()

    # Create a figure with num_pairs rows and 2 columns
    plt.figure(figsize=(10, 2*num_pairs))

    for i in range(min(num_pairs, len(labels))):
        # Display anchor image
        plt.subplot(num_pairs, 2, 2*i + 1)
        plt.imshow(anchor_images[i])
        plt.title('Anchor Image')
        plt.axis('off')

        # Display comparison image
        plt.subplot(num_pairs, 2, 2*i + 2)
        plt.imshow(compare_images[i])
        plt.title(f'{"Same" if labels[i] == 1 else "Different"} Person')
        plt.axis('off')

    plt.tight_layout()
    plt.show()