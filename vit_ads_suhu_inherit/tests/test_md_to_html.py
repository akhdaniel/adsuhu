from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestMdToHtml(TransactionCase):
    def test_md_to_html_wraps_table(self):
        md = "| A | B |\n| - | - |\n| 1 | 2 |"
        html = self.env["vit.general_object"].md_to_html(md)
        self.assertIn('<div class="table-responsive">', html)
        self.assertIn("<table", html)
        self.assertIn("</table></div>", html.replace("\n", ""))

    def test_md_to_html_without_table(self):
        md = "Just **bold** text."
        html = self.env["vit.general_object"].md_to_html(md)
        self.assertNotIn('table-responsive', html)
