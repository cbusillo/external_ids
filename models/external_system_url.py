from odoo import models, fields, api


class ExternalSystemUrl(models.Model):
    _name = "external.system.url"
    _description = "External System URL Template"
    _order = "sequence, code"

    name = fields.Char(required=True)
    code = fields.Char(required=True, help="Short code to reference this URL (e.g., store, admin, ticket)")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    system_id = fields.Many2one("external.system", required=True, ondelete="cascade")
    res_model_id = fields.Many2one(
        "ir.model",
        string="Applies To Model",
        help="Optional: restrict this template to a specific model (e.g., product.template). Leave empty for all.",
        index=True,
    )
    template = fields.Char(
        required=True,
        help=("URL template with tokens like {id}, {gid}, {model}, {name}, {code}, {base}. Example: {base}/admin/products/{id}"),
    )

    _sql_constraints = [
        (
            "code_unique_per_system",
            "unique(system_id, code, res_model_id)",
            "URL code must be unique per system/model",
        ),
    ]

    # Helpers ---------------------------------------------------------------
    @staticmethod
    def _sanitize_code(value: str) -> str:
        import re

        v = (value or "").lower()
        v = re.sub(r"[^a-z0-9_\s-]", "", v)
        v = re.sub(r"[\s-]+", "_", v).strip("_")
        return v

    @api.onchange("name")
    def _onchange_name_autofill_code(self) -> None:
        for rec in self:
            if not rec.code:
                rec.code = self._sanitize_code(rec.name)

    def write(self, vals):
        if "code" in vals and self and not self.env.context.get("allow_url_code_write"):
            # Disallow changing code outside of the rename wizard
            vals = dict(vals)
            vals.pop("code", None)
        return super().write(vals)

    def action_open_rename_wizard(self) -> dict:
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Rename URL Key",
            "res_model": "external.system.url.rename.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_url_id": self.id,
                "default_new_code": self.code,
            },
        }

    @api.constrains("template")
    def _check_template_tokens(self) -> None:
        allowed = {
            "id": "123",
            "gid": "gid://example/Model/123",
            "model": "res.partner",
            "name": "Record Name",
            "code": "shopify",
            "base": "https://example.com",
        }
        for rec in self:
            try:
                (rec.template or "").format(**allowed)
            except KeyError as e:  # unknown token
                raise ValueError(f"Unknown token {e} in URL template. Allowed: {', '.join(sorted(allowed))}.")
