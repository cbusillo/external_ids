from odoo import models


class HrEmployee(models.Model):
    _inherit = ["hr.employee", "external.id.mixin"]
