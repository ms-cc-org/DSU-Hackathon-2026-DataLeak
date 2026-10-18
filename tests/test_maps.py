"""Imagery configuration and missing county coverage use actual local geometry."""

import unittest

import pandas as pd

from web.maps import countyMapData, imageryUrl, resultMap


class CountyMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.table = pd.DataFrame([{"fips": "19123", "amount": 100}, {"fips": "19123", "amount": 200}])

    def testAllStateBoundariesRemainAndMissingCountiesAreNotZeroed(self) -> None:
        geometry, rows = countyMapData(self.table, "IA", "amount")
        self.assertEqual(len(geometry["features"]), 99)
        self.assertEqual(rows.loc[rows["fips"].eq("19123"), "value"].iloc[0], 300)
        self.assertEqual(int(rows["value"].isna().sum()), 98)

    def testImageryHasAttributionAndSitsBelowCountyResults(self) -> None:
        figure = resultMap(self.table, "IA", "amount")
        layer = figure.layout.map.layers[0]
        self.assertEqual(layer.source, (imageryUrl,))
        self.assertEqual(layer.below, "traces")
        self.assertEqual(layer.sourceattribution, "U.S. Geological Survey")
        self.assertEqual(len(figure.data), 2)

    def testOfflineAlternativeUsesLocalOutlinesWithoutTileRequests(self) -> None:
        figure = resultMap(self.table, "IA", "amount", satellite=False)
        self.assertTrue(all(trace.type == "scatter" for trace in figure.data))
        self.assertFalse(figure.layout.map.layers)


if __name__ == "__main__":
    unittest.main()
