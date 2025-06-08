"""
TODO: Not working yet
"""
import cv2
import numpy as np
from skimage.morphology import skeletonize
import matplotlib.pyplot as plt
import argparse


def extract_track_coordinates(image_path, resolution=1.0, origin=(0, 0)):
    """
    Extract inner, outer, and centerline coordinates from a binary track map image.
    
    Parameters:
    - image_path: Path to the binary image (white track on black background)
    - resolution: Meters per pixel (for ROS map scaling, default=1.0)
    - origin: Tuple (x, y) of the map origin in meters (default=(0, 0))
    
    Returns:
    - inner_coords: List of (x, y) coordinates for inner boundary (in meters)
    - outer_coords: List of (x, y) coordinates for outer boundary (in meters)
    - centerline_coords: List of (x, y) coordinates for centerline (in meters)
    """
    # Read the image in grayscale
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    print(f"Image shape: {image.shape}")
    
    # Ensure the image is binary (white track, black background)
    _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
    print(f"Binary image shape: {binary.shape}")
    
    # Invert if necessary (white should be 255, black 0)
    if np.mean(binary) < 128:  # If mostly dark, invert
        binary = 255 - binary
    
    # Find contours (boundaries) of the white track
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"Number of contours found: {len(contours)}")
    
    if not contours:
        raise ValueError("No contours found in the image. Check the image format and threshold.")
    
    print("Contours found, processing...")
    
    # Assume the largest contour is the track boundary
    track_contour = max(contours, key=cv2.contourArea)
    
    # Convert contour to a list of (x, y) points (in pixels)
    contour_points = track_contour.squeeze().tolist()
    
    # Separate inner and outer boundaries (simplified approach for a single contour)
    # For a simple closed loop, we can approximate inner and outer by offsetting
    # However, for precision, we'll use the contour as the outer boundary
    outer_coords_pixels = [(p[0], p[1]) for p in contour_points]
    
    # Create a mask for the track area
    mask = np.zeros_like(binary, dtype=np.uint8)
    cv2.drawContours(mask, [track_contour], -1, 255, thickness=cv2.FILLED)
    
    # Skeletonize to find the centerline (thinning the track to a single pixel width)
    skeleton = skeletonize(mask > 0).astype(np.uint8) * 255
    
    # Find contours of the skeleton (centerline)
    skeleton_contours, _ = cv2.findContours(skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not skeleton_contours:
        raise ValueError("No centerline (skeleton) found. Track may be too narrow or noisy.")
    
    # Use the largest skeleton contour as the centerline
    centerline_contour = max(skeleton_contours, key=cv2.contourArea)
    centerline_pixels = centerline_contour.squeeze().tolist()
    print(f"Centerline contour points: {len(centerline_pixels)}")
    
    # For inner boundary, erode the track slightly to shrink it inward
    kernel = np.ones((3, 3), np.uint8)
    eroded = cv2.erode(mask, kernel, iterations=1)
    eroded_contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not eroded_contours:
        raise ValueError("No inner boundary found after erosion. Track may be too narrow.")
    
    inner_contour = max(eroded_contours, key=cv2.contourArea)
    inner_coords_pixels = inner_contour.squeeze().tolist()
    print(f"Inner boundary contour points: {len(inner_coords_pixels)}")
    
    # Convert pixel coordinates to meters using resolution and origin
    def pixels_to_meters(pixel_coords, resolution, origin):
        print(f"Converting pixel coordinates to meters with resolution: {resolution} and origin: {origin}")
        meter_coords = []
        for x, y in pixel_coords:
            # ROS convention: x increases right, y increases down in images, but up in ROS maps
            # Adjust y to match ROS (invert y-axis)
            meter_x = origin[0] + x * resolution
            meter_y = origin[1] - y * resolution  # Invert y for ROS compatibility
            meter_coords.append((meter_x, meter_y))
        return meter_coords
    
    # Convert all coordinates to meters
    inner_coords = pixels_to_meters(inner_coords_pixels, resolution, origin)
    outer_coords = pixels_to_meters(outer_coords_pixels, resolution, origin)
    centerline_coords = pixels_to_meters(centerline_pixels, resolution, origin)
    
    print(f"Inner boundary coordinates (in meters): {inner_coords}")
    
    # Optional: Visualize the results
    plt.figure(figsize=(10, 10))
    plt.imshow(binary, cmap='gray')
    
    # Plot boundaries and centerline
    inner_x, inner_y = zip(*[(y, x) for x, y in inner_coords])  # Swap for plotting
    outer_x, outer_y = zip(*[(y, x) for x, y in outer_coords])
    center_x, center_y = zip(*[(y, x) for x, y in centerline_coords])
    
    plt.plot(inner_y, inner_x, 'b-', label='Inner Boundary')
    plt.plot(outer_y, outer_x, 'r-', label='Outer Boundary')
    plt.plot(center_y, center_x, 'g-', label='Centerline')
    plt.legend()
    plt.title("Track Boundaries and Centerline")
    plt.axis('equal')
    plt.show()
    
    return inner_coords, outer_coords, centerline_coords

# Example usage
if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description='Extract track coordinates from bitmap')
        parser.add_argument('image_path', help='Path to the track image (PGM or PNG)')
        parser.add_argument('--resolution', '-r', type=float, help='Map resolution in meters/pixel')

        args = parser.parse_args()
        
        # Specify your image path, resolution (meters/pixel), and origin (meters)
        image_path = args.image_path
        resolution = args.resolution
        origin = (0, 0)  # Example: origin at (0, 0) meters
        
        print(f"Starting to process image: {image_path}")
        inner, outer, centerline = extract_track_coordinates(image_path, resolution, origin)
        
        print("Inner Boundary Coordinates (meters):", inner)
        print("Outer Boundary Coordinates (meters):", outer)
        print("Centerline Coordinates (meters):", centerline)
        
    except Exception as e:
        print(f"Error: {e}")