from odoo.tests.common import TransactionCase
from odoo.addons.vit_ads_suhu.tests.common import VitAdsSuhuCommon

from odoo.exceptions import UserError
from odoo.tests import tagged

import logging
_logger = logging.getLogger(__name__)

@tagged('post_install', '-at_install')
class VideoVariantTestCase(VitAdsSuhuCommon):

	def test_vit_video_variant_count(cls):
		_logger.info(' -------------------- test record count -----------------------------------------')
		cls.assertEqual(
		    4,
		    len(cls.video_variants)
		)