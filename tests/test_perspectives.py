"""Aggregation checks for alternative business perspectives."""
from pathlib import Path
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dashboard_data import load_excel
from marketing import normalize_marketing, marketing_allocations
from perspectives import aggregate_sales, compare_sales, aggregate_marketing, flavour_label


class PerspectiveAggregationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.primary, cls.secondary, raw, _, _, expenses, *_ = load_excel(ROOT / 'Niamito_Master_Tables.xlsx')
        cls.marketing = normalize_marketing(raw)
        cls.allocations = marketing_allocations(expenses)

    def test_sales_dimensions_reconcile_independently(self):
        for dimension in ('product_family', 'flavour', 'market'):
            comparison = compare_sales(self.primary, self.secondary, dimension)
            self.assertEqual(comparison.primary_units.sum(), self.primary.bottles.sum())
            self.assertEqual(comparison.secondary_units.sum(), self.secondary.bottles_sold.sum())
            self.assertAlmostEqual(comparison.primary_revenue.sum(), self.primary.gross_revenue.sum())
            self.assertAlmostEqual(comparison.secondary_revenue.sum(), self.secondary.sellout_revenue.sum())
        retailers = aggregate_sales(self.secondary, 'retailer', 'secondary')
        self.assertAlmostEqual(retailers.secondary_revenue.sum(), self.secondary.sellout_revenue.sum())

    def test_absent_stage_unknown_groups_and_returns_stay_visible(self):
        primary = pd.DataFrame([
            {'market': 'SI', 'bottles': 10, 'gross_revenue': 30},
            {'market': 'SI', 'bottles': -2, 'gross_revenue': -6},
            {'market': None, 'bottles': 0, 'gross_revenue': 5},
        ])
        secondary = pd.DataFrame([{'market': 'HR', 'bottles_sold': 3, 'sellout_revenue': 12}])
        data = compare_sales(primary, secondary, 'market').set_index('market')
        self.assertEqual(data.loc['SI', 'primary_units'], 8)
        self.assertEqual(data.loc['Unassigned', 'primary_revenue'], 5)
        self.assertTrue(pd.isna(data.loc['HR', 'primary_revenue']))
        self.assertEqual(data.primary_revenue.sum(), 29)

    def test_sku_prefixes_unify_names_without_dropping_unknowns(self):
        self.assertEqual(flavour_label('CKU05 - DE', 'anything'), 'UHT · Cookie')
        self.assertEqual(flavour_label('COU05-DE', 'anything'), 'UHT · Cocoa')
        self.assertEqual(flavour_label('XYZ', 'Seasonal product'), 'Seasonal product')

    def test_marketing_sources_never_blend(self):
        for dimension in ('segment', 'channel', 'retailer', 'product_family', 'market'):
            result = aggregate_marketing(self.marketing, self.allocations, 'Calendar detail', dimension)
            self.assertAlmostEqual(result.total_spend.sum(), self.marketing.total_spend.sum())
        result = aggregate_marketing(self.marketing, self.allocations, 'Product allocations', 'product_family')
        self.assertAlmostEqual(result.total_spend.sum(), self.allocations.total_spend.sum())
        m = pd.DataFrame({'segment': ['ATL', None], 'total_spend': [100, -25]})
        result = aggregate_marketing(m, pd.DataFrame(), 'Calendar detail', 'segment')
        self.assertEqual(result.total_spend.sum(), 75)
        self.assertIn('Unassigned', result.segment.values)


if __name__ == '__main__':
    unittest.main()
