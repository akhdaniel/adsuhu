"""
To perform the sample basic tests, execute this command:
    odoo-bin -c yourodoo.conf -d yourdb -u vit_ads_suhu --test-tags /vit_ads_suhu

When you have implemented the detailed test cases on your inherited addon, then execute this:
    odoo-bin -c yourodoo.conf -d yourdb -u vit_ads_suhu_inherited --test-tags /vit_ads_suhu_inherited

"""
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.tests import tagged

import logging
_logger = logging.getLogger(__name__)

@tagged('post_install', '-at_install')
class VitAdsSuhuCommon(TransactionCase):

	@classmethod
	def setUpClass(cls):
		# add env on cls and many other things
		super(VitAdsSuhuCommon, cls).setUpClass()

		# create the data for each tests. By doing it in the setUpClass instead
		# of in a setUp or in each test case, we reduce the testing time and
		# the duplication of code.