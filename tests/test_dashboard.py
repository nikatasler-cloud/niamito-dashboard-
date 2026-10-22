"""Regression checks against the repository's workbook and interactive controls."""
import unittest
from pathlib import Path
import sys
from datetime import date
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dashboard_data import load_excel
from marketing import normalize_marketing, filter_marketing, monthly_spend, marketing_allocations
from dashboard_ui import csv_bytes
from streamlit.testing.v1 import AppTest


class WorkbookRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.primary, cls.secondary, raw, _, _, cls.expenses, *_ = load_excel(ROOT / 'Niamito_Master_Tables.xlsx')
        cls.marketing = normalize_marketing(raw)

    def test_sales_totals_and_adjustments_preserved(self):
        self.assertEqual(len(self.primary),196)
        self.assertEqual(self.primary.bottles.sum(),219972)
        self.assertAlmostEqual(self.primary.gross_revenue.sum(),619272.44,places=2)
        self.assertEqual(len(self.secondary),6970)
        self.assertEqual(self.secondary.bottles_sold.sum(),192698)
        self.assertAlmostEqual(self.secondary.sellout_revenue.sum(),572210.77,places=2)
        p=self.primary[self.primary.week.dt.to_period('M') == '2026-09']
        s=self.secondary[self.secondary.week.dt.to_period('M') == '2026-09']
        self.assertEqual(p.bottles.sum(),20712)
        self.assertAlmostEqual(p.gross_revenue.sum(),51644.43,places=2)
        self.assertEqual(s.bottles_sold.sum(),13306)
        self.assertAlmostEqual(s.sellout_revenue.sum(),35965.11,places=2)
        self.assertTrue((self.secondary.bottles_sold < 0).any())
        self.assertTrue(((self.primary.bottles == 0) & (self.primary.gross_revenue != 0)).any())

    def test_summary_row_excluded_and_breakdowns_reconcile(self):
        m=self.marketing
        self.assertEqual(len(m),85)
        self.assertAlmostEqual(m.total_spend.sum(),91191.29,places=2)
        for field in ['market','product_family','segment','retailer','channel']:
            self.assertAlmostEqual(m.groupby(field).total_spend.sum().sum(),91191.29,places=2)
        self.assertAlmostEqual(monthly_spend(m).cumulative.iloc[-1],91191.29,places=2)
        self.assertTrue(m.attributed_sales.isna().all())
        self.assertTrue((m.market == 'Unassigned').any())
        self.assertTrue(m.possible_duplicate.any())

    def test_explicit_classification_shared_costs_and_filters(self):
        raw=pd.DataFrame([
            {'name':'SPAR & Mercator UHT','start':'2026-01-01','total_spend':100,'channel':'Events'},
            {'name':'brand campaign','start':'2026-02-01','total_spend':200,'channel':'Digital','market':'HR','product_family':'HPP','retailer':'Custom shop','segment':'ATL'},
            {'name':'refund','start':None,'total_spend':-20,'channel':'Digital'},
        ])
        m=normalize_marketing(raw)
        self.assertEqual(m.loc[0,'retailer'],'Multiple retailers')
        self.assertEqual(m.loc[0,'product_family'],'UHT')
        self.assertEqual(m.loc[1,'segment'],'ATL')
        self.assertEqual(m.loc[1,'retailer'],'Custom shop')
        self.assertEqual(m.total_spend.sum(),280)
        self.assertEqual(filter_marketing(m,families=['UHT']).total_spend.sum(),100)
        self.assertEqual(filter_marketing(m,markets=['HR']).total_spend.sum(),200)
        self.assertTrue(filter_marketing(m,query='[missing]').empty)
        self.assertEqual(monthly_spend(m).total_spend.sum(),300)
        self.assertEqual(len(normalize_marketing(pd.DataFrame())),0)

    def test_recorded_product_allocations_and_month_boundaries(self):
        allocation=marketing_allocations(self.expenses)
        self.assertAlmostEqual(allocation.total_spend.sum(),119908.70,places=2)
        self.assertEqual(set(allocation.product_family),{'Kaša','HPP','UHT'})
        july=marketing_allocations(self.expenses,'2026-07-01','2026-07-31')
        self.assertAlmostEqual(july.total_spend.sum(),19961.45,places=2)
        self.assertTrue(marketing_allocations(self.expenses,'2025-01-01','2025-12-31').empty)
        self.assertEqual(marketing_allocations(self.expenses,'2026-07-15','2026-07-16').total_spend.sum(),july.total_spend.sum())

    def test_csv_keeps_numeric_values_and_escapes_formula_strings(self):
        csv=csv_bytes(pd.DataFrame({'name':['=SUM(A1)','normal'],'amount':[-5,10]})).decode('utf-8-sig')
        self.assertIn("'=SUM(A1)",csv)
        self.assertIn(',-5',csv)


class InteractiveRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()

    def check_clean(self):
        self.assertEqual([x.message for x in self.app.exception],[])

    def test_controls_and_empty_states(self):
        at=self.app
        self.check_clean()
        self.assertIn('Overview',[x.label for x in at.tabs])
        at.sidebar.selectbox[0].select('All data').run(); self.check_clean()
        at.multiselect(key='mkt_product').set_value(['UHT']).run(); self.check_clean()
        at.multiselect(key='mkt_segment').set_value(['ATL']).run(); self.check_clean()
        self.assertTrue(any('No expenses match' in x.value for x in at.info))
        at.multiselect(key='mkt_product').set_value([])
        at.multiselect(key='mkt_segment').set_value([]).run(); self.check_clean()
        at.text_input(key='mkt_search').set_value('no record like this').run(); self.check_clean()
        at.text_input(key='mkt_search').set_value('').run()
        at.sidebar.multiselect[0].set_value(['Niamito Meal in a Bottle']).run(); self.check_clean()
        at.radio(key='metric_mode').set_value('Revenue (€)').run(); self.check_clean()
        for method in at.selectbox(key='fc_type_sel').options:
            at.selectbox(key='fc_type_sel').select(method).run(); self.check_clean()
        at.selectbox(key='fc_scenario_sel').select('Conservative (−20%)').run(); self.check_clean()
        at.sidebar.multiselect[0].set_value([]).run(); self.check_clean()
        at.sidebar.selectbox[0].select('Custom range').run(); self.check_clean()
        at.date_input[0].set_value((date(2026,9,1),date(2026,9,30))).run(); self.check_clean()
        self.assertTrue(any('No marketing expenses' in x.value for x in at.info))
        at.date_input[0].set_value((date(2024,1,1),date(2024,1,2))).run(); self.check_clean()
        at.date_input[0].set_value((date(2026,9,1),)).run(); self.check_clean()
        self.assertTrue(any('both a start and end date' in x.value for x in at.info))

    def test_original_hosting_entrypoint(self):
        at=AppTest.from_file(str(ROOT/'appreal.py'),default_timeout=60).run()
        self.assertEqual([x.message for x in at.exception],[])


if __name__ == '__main__':
    unittest.main()
