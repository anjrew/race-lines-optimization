import numpy as np
import cv2
import matplotlib.pyplot as plt
import argparse
from pathlib import Path
import csv

def extract_track_coordinates(image_path: str, output_path=None, visualize=True):
    """
    Extract track coordinates from a bitmap image (PGM or PNG).
    
    Args:
        image_path: Path to the input image file
        output_path: Path to save the coordinates CSV file (optional)
        visualize: Whether to display visualization of the extracted coordinates
    
    Returns:
        tuple: (centerline_coords, boundary_coords)
    """
    # Load the image
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    print(f"Loaded image with shape: {img.shape}")
    
    # Threshold the image to create a binary image
    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    
    # Invert if the track is white (assuming track is darker than background)
    if np.mean(binary) > 127:
        binary = 255 - binary
    
    # Find contours - for boundary extraction
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Find the largest contour (assuming it's the track)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Simplify the contour to reduce number of points (Douglas-Peucker algorithm)
    epsilon = 0.005 * cv2.arcLength(largest_contour, True)
    boundary_points = cv2.approxPolyDP(largest_contour, epsilon, True)
    
    # Extract boundary coordinates
    boundary_coords = []
    for point in boundary_points:
        x, y = point[0]  # type: ignore
        boundary_coords.append((x, y))
    
    # Skeletonize to get centerline
    # Distance transform + adaptive thresholding
    dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
    
    # Normalize for visualization
    dist_norm = cv2.normalize(dist_transform, None, 0, 1.0, cv2.NORM_MINMAX)
    
    # Improve skeleton by using an adaptive threshold based on max distance
    max_dist = np.max(dist_transform[binary > 0])  # Max distance within track
    factor = 0.5 ## Factor
    thresh_value = max_dist * factor  # Threshold at half the max distance (adjustable)
    _, skeleton = cv2.threshold(dist_transform, thresh_value, 255, cv2.THRESH_BINARY)
    skeleton = skeleton.astype(np.uint8)
    
    # Optional: Thin the skeleton with a single erosion step to refine it
    kernel = np.ones((3, 3), np.uint8)
    skeleton = cv2.erode(skeleton, kernel, iterations=1)
    
    # Find centerline points
    centerline_points = np.where(skeleton > 0)
    centerline_coords = [(x, y) for y, x in zip(centerline_points[0], centerline_points[1])]
    
    # Sort centerline points to follow the track
    if len(centerline_coords) > 1:
        sorted_centerline = [centerline_coords[0]]
        remaining = centerline_coords[1:]
        
        while remaining:
            last_point = sorted_centerline[-1]
            distances = [np.sqrt((p[0] - last_point[0])**2 + (p[1] - last_point[1])**2) for p in remaining]
            closest_idx = np.argmin(distances)
            sorted_centerline.append(remaining[closest_idx])
            remaining.pop(closest_idx)
            
            # Break if remaining points are too far (gaps in track)
            if distances[closest_idx] > 20 and len(sorted_centerline) > len(centerline_coords) // 2:
                break
                
        centerline_coords = sorted_centerline
    
    # Save to CSV if output path is provided
    if output_path:
        with open(output_path / 'centerline.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['x', 'y'])
            writer.writerows(centerline_coords)
            
        with open(output_path / 'boundary.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['x', 'y'])
            writer.writerows(boundary_coords)

        plt.imsave(output_path / 'distance_transform.png', dist_norm, cmap='hot')
        plt.imsave(output_path / 'centerline.png', cv2.cvtColor(skeleton, cv2.COLOR_GRAY2RGB))
        plt.imsave(output_path / 'binary.png', binary, cmap='gray')
        plt.imsave(output_path / 'track.png', cv2.cvtColor(img, cv2.COLOR_GRAY2RGB))
        plt.imsave(output_path / 'track_with_coords.png', cv2.cvtColor(img, cv2.COLOR_GRAY2RGB))    
    
    # Visualize results
    if visualize:
        plt.figure(figsize=(12, 10))
        
        # # Original image
        # plt.subplot(2, 2, 1)
        # plt.imshow(img, cmap='gray')
        # plt.title('Original Track Image')
        
        # # Binary image
        # plt.subplot(2, 2, 2)
        # plt.imshow(binary, cmap='gray')
        # plt.title('Binary Track Image')
        
        # # Distance transform
        # plt.subplot(2, 2, 3)
        # plt.imshow(dist_norm, cmap='hot')
        # plt.title('Distance Transform')
        
        # Result with coordinates
        # plt.subplot(2, 2, 4)
        plt.imshow(img, cmap='gray')
        centerline_x = [p[0] for p in centerline_coords]
        centerline_y = [p[1] for p in centerline_coords]
        plt.plot(centerline_x, centerline_y, 'g-', linewidth=2, label='Centerline')
        boundary_x = [p[0] for p in boundary_coords]
        boundary_y = [p[1] for p in boundary_coords]
        plt.plot(boundary_x, boundary_y, 'b-', linewidth=2, label='Boundary')
        plt.title('Extracted Track Coordinates')
        plt.legend()
        
        plt.tight_layout()
        plt.show()
        if output_path:
            plt.savefig(output_path / 'track_with_coords.png')
    
    return centerline_coords, boundary_coords

def create_ros_map_yaml(pgm_path, output_path, resolution=0.05):
    """
    Create a ROS map YAML file for the PGM image.
    
    Args:
        pgm_path: Path to the PGM file
        output_path: Path to save the YAML file
        resolution: Map resolution in meters/pixel
    """
    yaml_content = f"""image: {Path(pgm_path).name}
resolution: {resolution}
origin: [0.0, 0.0, 0.0]
occupied_thresh: 0.65
free_thresh: 0.196
negate: 0
"""
    with open(output_path / f"{Path(pgm_path).stem}.yaml", 'w') as file:
        file.write(yaml_content)

def convert_to_ros_coordinates(coords, image_height, resolution=0.05):
    """
    Convert image coordinates to ROS coordinates.
    
    Args:
        coords: List of (x, y) coordinates in image frame
        image_height: Height of the image
        resolution: Map resolution in meters/pixel
    
    Returns:
        List of (x, y) coordinates in ROS frame
    """
    return [(x * resolution, (image_height - y) * resolution) for x, y in coords]

def main():
    parser = argparse.ArgumentParser(description='Extract track coordinates from bitmap')
    parser.add_argument('image_path', help='Path to the track image (PGM or PNG)')
    parser.add_argument('--output', '-o', help='Directory to save output files', default='./tmp')
    parser.add_argument('--resolution', '-r', type=float, default=0.05, help='Map resolution in meters/pixel')
    parser.add_argument('--no-viz', action='store_true', help='Disable visualization')
    
    args = parser.parse_args()
    
    image_path = Path(args.image_path)
    output_path = Path(args.output)
    output_path.mkdir(exist_ok=True)
    
    print(f"Processing {image_path}...")
    
    # Extract track coordinates
    centerline, boundary = extract_track_coordinates(
        image_path, 
        output_path, 
        visualize=not args.no_viz
    )
    
    # Load image to get dimensions
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    
    # Convert to ROS coordinates
    ros_centerline = convert_to_ros_coordinates(centerline, img.shape[0], args.resolution)
    ros_boundary = convert_to_ros_coordinates(boundary, img.shape[0], args.resolution)
    
    # Save ROS coordinates
    with open(output_path / 'ros_centerline.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['x', 'y'])
        writer.writerows(ros_centerline)
        
    with open(output_path / 'ros_boundary.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['x', 'y'])
        writer.writerows(ros_boundary)
    
    # Create ROS map YAML file if input is PGM
    if image_path.suffix.lower() == '.pgm':
        create_ros_map_yaml(image_path, output_path, args.resolution)
    
    print(f"Extracted {len(centerline)} centerline points and {len(boundary)} boundary points")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()