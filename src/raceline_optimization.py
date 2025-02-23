import copy
import logging
import numpy as np
from shapely.geometry import Point, Polygon


class RacelineOptimization:

    def __init__(self, center_line, inline, outline):
        self.center_line = center_line
        self.inline = inline
        self.outline = outline

    def get_optimized_race_line(self, iterations=100):
        logging.info(f"Optimizing race line with {iterations} on {self.center_line.shape[0]} points.")
        race_line = copy.deepcopy(self.center_line[:-1])  # Use this for centerline being outer bound
        for i in range(iterations):
            race_line = self.improve_race_line(race_line)
            if i % 20 == 0: logging.info(f"RacelineOptimization: Iteration {i}")
        return race_line

    def menger_curvature(pt1, pt2, pt3, atol=1e-3):

        vec21 = np.array([pt1[0] - pt2[0], pt1[1] - pt2[1]])
        vec23 = np.array([pt3[0] - pt2[0], pt3[1] - pt2[1]])

        norm21 = np.linalg.norm(vec21)
        norm23 = np.linalg.norm(vec23)

        theta = np.arccos(np.dot(vec21, vec23) / (norm21 * norm23))
        if np.isclose(theta - np.pi, 0.0, atol=atol):
            theta = 0.0

        dist13 = np.linalg.norm(vec21 - vec23)

        return 2 * np.sin(theta) / dist13

    def improve_race_line(self, old_line, xi_iterations=4):
        # start with the center line
        new_line = copy.deepcopy(old_line)
        ls_inner_border = Polygon(self.inline)
        ls_outer_border = Polygon(self.outline)
        for i in range(0, len(new_line)):
            xi = new_line[i]
            npoints = len(new_line)
            prevprev = (i - 2 + npoints) % npoints
            prev = (i - 1 + npoints) % npoints
            nexxt = (i + 1 + npoints) % npoints
            nexxtnexxt = (i + 2 + npoints) % npoints
            # print("%d: %d %d %d %d %d" % (npoints, prevprev, prev, i, nexxt, nexxtnexxt))
            ci = RacelineOptimization.menger_curvature(new_line[prev], xi, new_line[nexxt])
            c1 = RacelineOptimization.menger_curvature(new_line[prevprev], new_line[prev], xi)
            c2 = RacelineOptimization.menger_curvature(xi, new_line[nexxt], new_line[nexxtnexxt])
            target_ci = (c1 + c2) / 2
            # print("i %d ci %f target_ci %f c1 %f c2 %f" % (i, ci, target_ci, c1, c2))

            # Calculate prospective new track position, start at half-way (curvature zero)
            xi_bound1 = copy.deepcopy(xi)
            xi_bound2 = ((new_line[nexxt][0] + new_line[prev][0]) / 2.0, (new_line[nexxt][1] + new_line[prev][1]) / 2.0)
            p_xi = copy.deepcopy(xi)
            for j in range(0, xi_iterations):
                p_ci = RacelineOptimization.menger_curvature(new_line[prev], p_xi, new_line[nexxt])
                # print("i: {} iter {} p_ci {} p_xi {} b1 {} b2 {}".format(i,j,p_ci,p_xi,xi_bound1, xi_bound2))
                if np.isclose(p_ci, target_ci):
                    break
                if p_ci < target_ci:
                    # too flat, shrinking track too much
                    xi_bound2 = copy.deepcopy(p_xi)
                    new_p_xi = ((xi_bound1[0] + p_xi[0]) / 2.0, (xi_bound1[1] + p_xi[1]) / 2.0)
                    if Point(new_p_xi).within(ls_inner_border) or not Point(new_p_xi).within(ls_outer_border):
                        xi_bound1 = copy.deepcopy(new_p_xi)
                    else:
                        p_xi = new_p_xi
                else:
                    # too curved, flatten it out
                    xi_bound1 = copy.deepcopy(p_xi)
                    new_p_xi = ((xi_bound2[0] + p_xi[0]) / 2.0, (xi_bound2[1] + p_xi[1]) / 2.0)

                    # If iteration pushes the point beyond the border of the track,
                    # just abandon the refinement at this point.  As adjacent
                    # points are adjusted within the track the point should gradually
                    # make its way to a new position.  A better way would be to use
                    # a projection of the point on the border as the new bound.  Later.
                    if Point(new_p_xi).within(ls_inner_border) or not Point(new_p_xi).within(ls_outer_border):
                        xi_bound2 = copy.deepcopy(new_p_xi)
                    else:
                        p_xi = new_p_xi
            new_xi = p_xi
            # New point which has mid-curvature of prev and next points but may be outside of track
            # print((new_line[i], new_xi))
            new_line[i] = new_xi
        return new_line



