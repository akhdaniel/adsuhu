from odoo.tests.common import TransactionCase
from odoo.addons.vit_ads_suhu.tests.common import VitAdsSuhuCommon

from odoo.exceptions import UserError
from odoo.tests import tagged

import logging
_logger = logging.getLogger(__name__)

@tagged('post_install', '-at_install')
class ImageVariantTestCase(VitAdsSuhuCommon):

	def test_vit_image_variant_count(cls):
		_logger.info(' -------------------- test record count -----------------------------------------')
		cls.assertEqual(
		    4,
		    len(cls.image_variants)
		)