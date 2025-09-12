from typing import Self

from odoo import api, models, fields


class ExternalIdMixin(models.AbstractModel):
    _name = "external.id.mixin"
    _description = "External ID Mixin"

    external_ids = fields.One2many(
        "external.id",
        compute="_compute_external_ids",
        inverse="_inverse_external_ids",
        string="External IDs",
        help="External system IDs for this record",
    )

    def _compute_external_ids(self) -> None:
        ExternalId = self.env["external.id"]
        if not self:
            return
        domain = [("res_model", "=", self._name), ("res_id", "in", self.ids), ("active", "=", True)]
        grouped: dict[int, models.Model] = {}
        for rec in ExternalId.search(domain):
            if rec.res_id in grouped:
                grouped[rec.res_id] |= rec
            else:
                grouped[rec.res_id] = rec
        for record in self:
            record.external_ids = grouped.get(record.id, self.env["external.id"])

    def _inverse_external_ids(self) -> None:
        ExternalId = self.env["external.id"]
        for rec in self:
            if not rec.id:
                continue

            desired = ExternalId.browse()  # the records that should remain linked after save

            # Create or update listed External IDs from the UI
            for ext in rec.external_ids:
                # Collect incoming values from the virtual line (works for both new and existing lines)
                vals = ext._convert_to_write(ext._cache)
                vals["res_model"] = rec._name
                vals["res_id"] = rec.id

                if not ext.id:
                    new_rec = ExternalId.create(vals)
                    desired |= new_rec
                else:
                    # Persist edits made inline (e.g., system_id/external_id/active/notes)
                    ext.write(vals)
                    desired |= ext

            # Remove links that were dropped in the UI by archiving the extras
            linked = ExternalId.search(
                [
                    ("res_model", "=", rec._name),
                    ("res_id", "=", rec.id),
                ]
            )
            to_unlink = linked - desired
            if to_unlink:
                # Archive instead of unlink to honor data retention rule
                to_unlink.write({"active": False})

    def get_external_system_id(self, system_code: str) -> str | None:
        self.ensure_one()
        external_id = self.external_ids.filtered(lambda x: x.system_id.code == system_code and x.active)
        return external_id.external_id if external_id else None

    def set_external_id(self, system_code: str, external_id_value: str) -> bool:
        self.ensure_one()
        ExternalId = self.env["external.id"]
        System = self.env["external.system"]

        system = System.search([("code", "=", system_code)], limit=1)
        if not system:
            raise ValueError(f"External system with code '{system_code}' not found")

        existing = self.external_ids.filtered(lambda x: x.system_id == system)

        sanitized = (external_id_value or "").strip()

        if existing:
            existing.external_id = sanitized
        else:
            ExternalId.create(
                {
                    "res_model": self._name,
                    "res_id": self.id,
                    "system_id": system.id,
                    "external_id": sanitized,
                }
            )

        return True

    @api.model
    def search_by_external_id(self, system_code: str, external_id_value: str) -> Self:
        ExternalId = self.env["external.id"]
        System = self.env["external.system"]

        system = System.search([("code", "=", system_code)], limit=1)
        if not system:
            return self.browse()

        external_id_record = ExternalId.search(
            [
                ("res_model", "=", self._name),
                ("system_id", "=", system.id),
                ("external_id", "=", external_id_value),
            ],
            limit=1,
        )

        if external_id_record:
            return self.browse(external_id_record.res_id)
        return self.browse()

    def action_view_external_ids(self) -> "odoo.values.ir_actions_act_window":
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"External IDs for {self.display_name}",
            "res_model": "external.id",
            "view_mode": "list,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
            },
        }
