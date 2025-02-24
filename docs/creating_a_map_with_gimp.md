# Creating a map file

## Introduction

1. ROS with output a .pgm file for the map
2. Open the .png file in GIMP and draw the map

Open the File:
Launch GIMP and go to File → Open to load your .pgm file. Since .pgm files are grayscale, it will open as such.

Convert to RGB (Optional):
If you plan to use color or apply certain filters, convert the image by going to Image → Mode → RGB.

Enhance the Image:

Adjust Brightness/Contrast: Use Colors → Brightness-Contrast or Colors → Levels to tweak the overall exposure and contrast.
Improve Details: Apply Colors → Curves for more fine-tuned adjustments.
Clean Up Artifacts: Use the Eraser, Healing, or Clone Tool to remove unwanted spots or lines.
Refine Specific Areas:
Zoom in to work on detailed sections. Use selection tools (like the lasso or rectangle select) to isolate areas for localized adjustments.

Save/Export Your Work:
When finished, go to File → Export As. If you need to keep the file in .pgm format (for ROS compatibility), ensure you select .pgm as the file type and verify any accompanying settings.

These steps should help you refine your ROS map image in GIMP effectively.