import argparse
import cv2
import json
import logging
import numpy as np
import os
import shapely
from tkinter.filedialog import askdirectory
from raceline_optimization import RacelineOptimization


class TrackFromBitmap:

    def __init__(self, track_folder: str, scale=0.2, dist_to_border=0.35,
                 line_thickness=4):
        track_folder = os.path.normpath(track_folder)

        print("Track folder", track_folder)

        track_name = os.path.basename(track_folder)
        print("Track name", track_name)
        track_scale = json.load(open(os.path.join(folder, "track.json")))["scale"]
        filename = os.path.join(folder, f"{track_name}.png")
        print("Getting track from bitmap", filename)
        self.bitmap = cv2.imread(filename)
        logging.info(f"Start conversion of bitmap {filename}.")
        self.contours = []
        gray = cv2.cvtColor(self.bitmap, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]
        contours = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        output = self.bitmap.copy()
        for c in contours[0]:
            c = np.squeeze(c,axis=(1,))
            if c.shape[0] < 100:
                continue
            approx = np.squeeze(cv2.approxPolyDP(c, 2, closed=True), axis=(1,))
            self.contours.append(approx)

        skel_img = cv2.ximgproc.thinning(thresh)
        skel_contour = cv2.findContours(skel_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        c = np.squeeze(skel_contour[0][0], axis=(1,))
        skel_contour_approx = np.squeeze(cv2.approxPolyDP(c, 1, closed=True), axis=(1,))
        self.contours.append(skel_contour_approx)

        (x, y, w, h) = cv2.boundingRect(self.contours[0])
        self.contours.append(np.asarray([(x-10, y-10), (x+w+10, y-10), (x+w+10, y+h+10), (x-10, y+h+10)]))

        contours = [c * scale for c in self.contours]
        self.contours = []
        for c in contours:
            polygon = shapely.geometry.Polygon(c)
            if not shapely.geometry.polygon.orient(polygon):
                self.contours.append(np.flip(c, axis=0))
            else:
                self.contours.append(c)

        inline = shapely.Polygon(self.contours[1]).buffer(dist_to_border/track_scale)
        outline = shapely.Polygon(self.contours[0]).buffer(-dist_to_border/track_scale)
        raceline_optimizer = RacelineOptimization(self.contours[2],
                                                  inline,
                                                  outline)
        self.contours.append(raceline_optimizer.get_optimized_race_line(iterations=500))
        colors = [
            (255, 255, 0),
            (0, 255, 255),
            (255, 0, 255),
            (0, 0, 255),
            (255, 0, 0)
        ]
        for contour, color in zip(self.contours, colors):
            try:
                scaled_contour = np.int32((contour / scale).reshape((-1, 1, 2)))
                cv2.polylines(output, [scaled_contour], -1, color=color, thickness=line_thickness)
            except Exception as e:
                print(e)

        cv2.imshow("Calculated polygons", output)
        cv2.imwrite(filename.replace(".png", "_lines.png"), output)
        cv2.waitKey(0)
        self.export(folder, track_name)

    def export(self, folder, track_name):
        logging.info(f"Exporting polygons of track {track_name} into folder {folder}.")
        files = [f"{track_name}_outline.csv",
                 f"{track_name}_inline.csv",
                 f"{track_name}_centerline.csv",
                 f"{track_name}_boundingbox.csv",
                 f"{track_name}_raceline.csv"]
        for file, contour in zip(files, self.contours):
            try:
                np.savetxt(os.path.join(folder, file), contour, delimiter=";")
                logging.info(f"Successfully wrote into {file} ({contour.shape[0]} points).")
            except Exception as e:
                logging.error(f"Exception while writing {file}: {e}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Track from bitmap')
    parser.add_argument('--folder', help='folder path', type=str, required=False, default="")
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    args = parser.parse_args()
    folder = args.folder

    if not os.path.exists(folder):
        folder = askdirectory()
    if folder is not None and os.path.exists(folder):
        converter = TrackFromBitmap(folder)
