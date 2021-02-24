import logging
import os
import datetime as dt
from unittest import TestCase

from tools import PortfolioManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s  %(name)s  %(levelname)8s: %(message)s')

logger = logging.getLogger(__name__)


class PortforlioManagerTest(TestCase):

    def setUp(self) -> None:
        self.tx_file = os.path.join('fixtures', 'transactions-from-14122014-to-08022021.csv')
        self.special_prices = {'TKY': 195.3903}

    def test_constructor(self):

        pm = PortfolioManager(initial_amount=0.0,
                              tx_file=self.tx_file,
                              from_=dt.date(2017, 1, 5),
                              to_=dt.date(2021, 2, 5))

        history = pm.portfolio_history

        self.assertTrue(True)
