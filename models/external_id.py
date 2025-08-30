from typing import Any, Optional
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ExternalId(models.Model):
    _name = "external.id"
    _description = "External System IDs"
    _order = "system_id, id"
    _rec_name = "display_name"

    res_model = fields.Char(string="Model", required=True, index=True, help="The model this external ID belongs to")
    res_id = fields.Integer(string="Record ID", required=True, index=True, help="The ID of the record in the model")
    reference = fields.Reference(
        selection="_reference_models",
        compute="_compute_reference",
        inverse="_inverse_reference",
        search="_search_reference",
    )

    system_id = fields.Many2one(
        "external.system", string="External System", required=True, ondelete="restrict", domain=[("active", "=", True)]
    )
    external_id = fields.Char(string="External ID", required=True, help="The ID of this record in the external system")
    display_name = fields.Char(compute="_compute_display_name", store=True)
    record_name = fields.Char(compute="_compute_record_name", store=True)

    notes = fields.Text(help="Additional notes about this external ID")
    active = fields.Boolean(default=True, help="If unchecked, this external ID is considered inactive")
    last_sync = fields.Datetime(help="Last time this ID was synchronized with the external system")

    _sql_constraints = [
        (
            "unique_record_per_system",
            "UNIQUE(res_model, res_id, system_id)",
            "Each record can have only one ID per external system!",
        ),
        ("unique_external_id_per_system", "UNIQUE(system_id, external_id)", "This external ID already exists for this system!"),
    ]

    @api.model
    def _reference_models(self) -> list[tuple[str, str]]:
        reference_models = []
        for model_name in self.env:
            model = self.env[model_name]
            if hasattr(model, "_inherit") and "external.id.mixin" in (
                model._inherit if isinstance(model._inherit, list) else [model._inherit]
            ):
                reference_models.append((model_name, model._description or model_name))
        return reference_models

    @api.depends("res_model", "res_id")
    def _compute_reference(self) -> None:
        for record in self:
            if record.res_model and record.res_id:
                record.reference = f"{record.res_model},{record.res_id}"
            else:
                record.reference = False

    def _inverse_reference(self) -> None:
        for record in self:
            if record.reference:
                ref_model = record.reference
                record.res_model = getattr(ref_model, "_name", False)
                record.res_id = getattr(ref_model, "id", False)
            else:
                record.res_model = False
                record.res_id = False

    @staticmethod
    def _search_reference(operator: str, value: Any) -> list[tuple[str, str, Any]]:
        if operator == "=" and value:
            return [("res_model", "=", value._name), ("res_id", "=", value.id)]
        return []

    @api.depends("res_model", "res_id")
    def _compute_record_name(self) -> None:
        for record in self:
            if record.res_model and record.res_id:
                try:
                    referenced_record = self.env[record.res_model].browse(record.res_id)
                    if referenced_record.exists():
                        record.record_name = referenced_record.display_name
                    else:
                        record.record_name = f"[Deleted {record.res_model}]"
                except (KeyError, AttributeError, ValueError):
                    record.record_name = f"[Invalid {record.res_model}]"
            else:
                record.record_name = ""

    @api.depends("system_id", "external_id", "record_name")
    def _compute_display_name(self) -> None:
        for record in self:
            if record.system_id and record.external_id:
                prefix = record.system_id.id_prefix or ""
                record_info = f" ({record.record_name})" if record.record_name else ""
                record.display_name = f"{record.system_id.name}: {prefix}{record.external_id}{record_info}"
            else:
                record.display_name = record.external_id or ""

    @api.constrains("external_id", "system_id")
    def _check_id_format(self) -> None:
        for record in self:
            if record.system_id.id_format:
                import re

                if not re.match(record.system_id.id_format, record.external_id):
                    raise ValidationError(
                        f"External ID '{record.external_id}' does not match the expected format "
                        f"for {record.system_id.name}: {record.system_id.id_format}"
                    )

    def action_sync(self) -> dict[str, Any]:
        self.ensure_one()
        self.last_sync = fields.Datetime.now()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Sync Complete",
                "message": f"Synchronized {self.display_name}",
                "type": "success",
            },
        }

    @api.model
    def get_record_by_external_id(self, system_code: str, external_id: str) -> Optional[models.Model]:
        System = self.env["external.system"]
        system = System.search([("code", "=", system_code)], limit=1)

        if not system:
            return None

        external_record = self.search(
            [("system_id", "=", system.id), ("external_id", "=", external_id), ("active", "=", True)], limit=1
        )

        if external_record and external_record.res_model and external_record.res_id:
            try:
                record = self.env[external_record.res_model].browse(external_record.res_id)
                if record.exists():
                    return record
            except (KeyError, AttributeError, ValueError):
                pass

        return None

    @api.ondelete(at_uninstall=False)
    def _unlink_except_active(self) -> None:
        if any(record.active for record in self):
            raise ValidationError("Cannot delete active external IDs. Please archive them first.")
