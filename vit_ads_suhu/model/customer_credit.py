#!/usr/bin/python
#-*- coding: utf-8 -*-

STATES = [("draft", "Draft"),("done", "Done")]
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class customer_credit(models.Model):

    _name = "vit.customer_credit"
    _description = "vit.customer_credit"


    def action_reload_view(self):
        pass

    name = fields.Char( required=True, copy=False, default="New", readonly=True,  string=_("Name"))
    date_time = fields.Datetime( readonly="state=='draft'",  string=_("Date Time"))
    credit = fields.Float( readonly="state=='draft'",  string=_("Credit"))
    is_usage = fields.Boolean( readonly="state=='draft'",  string=_("Is Usage"), default=True)
    state = fields.Selection(selection=STATES,  readonly=True, default=STATES[0][0],  string=_("State"))
    ref = fields.Char( readonly="state=='draft'",  string=_("Ref"))


    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if not val.get("name", False) or val["name"] == "New":
                val["name"] = self.env["ir.sequence"].next_by_code("vit.customer_credit") or "Error Number!!!"
        return super(customer_credit, self).create(vals)

    def action_confirm(self):
        current_index=0
        current_state=self.state
        for st in STATES:

            current_index += 1
            if current_index >= len(STATES):
                current_index -= 1

            if current_state == st[0]:
                self.state = STATES[current_index][0]

    def action_cancel(self):
        self.state = STATES[0][0]

    def unlink(self):
        for me_id in self :
            if me_id.state != STATES[0][0]:
                raise UserError("Cannot delete non draft record!")
        return super(customer_credit, self).unlink()

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(customer_credit, self).copy(default)

    customer_id = fields.Many2one(comodel_name="res.partner",  readonly="state=='draft'",  string=_("Customer"))
