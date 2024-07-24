#!/usr/bin/env python

import shapely
import geojson
import os
import pandas as pd
import json
import sys

class IntersectParser():
    def __init__(self, path_to_transect, path_to_shoreline, save_path) -> None:
        self.path_to_transect = path_to_transect
        self.path_to_shoreline = path_to_shoreline
        self.save_path = save_path

        self.shoreline_intersects = self.load_shoreline()
        self.transects = self.load_transects()
        self.segments = []


    def load_shoreline(self) -> pd.DataFrame:
        shoreline_intersects = pd.read_csv(self.path_to_shoreline, index_col='dates')
        shoreline_intersects = shoreline_intersects.loc[:, ~shoreline_intersects.columns.str.contains('^Unnamed')]

        return shoreline_intersects

    def load_transects(self) -> dict:
        with open(self.path_to_transect, 'r') as f:
            gj: geojson.FeatureCollection = geojson.load(f)

        transects = { feat.properties['name']: shapely.LineString(feat.geometry.coordinates) for feat in gj.features}
        return transects

    def extract_segments(self):
        for shoreline in self.shoreline_intersects.iterrows():
            shoreline_date = shoreline[0]
            transect_intersects: pd.Series = list(shoreline[1].items())

            segment = []
            for idx, (label, intersect) in enumerate(transect_intersects):
                transect_name = label.split(' ')[1]
                transect_geom = self.transects[transect_name]

                if pd.isna(intersect) or idx == len(transect_intersects) - 1:
                    if len(segment) <= 1:
                        segment = [] 
                    else:
                        self.segments.append(
                            geojson.Feature(id=shoreline_date, 
                                            geometry=shapely.LineString(segment)
                            )
                        )
                        segment = []
                else:
                    intersection_point = transect_geom.interpolate(intersect)
                    segment.append(intersection_point)


    def parse(self):
        self.extract_segments()
        segments = geojson.FeatureCollection(self.segments) 
        segments.crs = self.transects.crs 

        with open(self.save_path, 'w') as f:
            output =json.dumps(segments, indent=2)
            f.write(output)



def assertfile_type_and_exists(file_path, expected_extension):
    exists = os.path.isfile(file_path)
    if exists:
        _, extension = os.path.splitext(file_path)
        is_correct_extension = extension == expected_extension

        if is_correct_extension:
            return True
        else:
            message = f"{file_path} has wrong extension. expected {expected_extension}"
            sys.exit((1, message))
    else: 
        sys.exit((1, f"cant find file {file_path}"))

if __name__ == "__main__":
