from typing import Self

from odoo import api, models


class ExternalIdMixin(models.AbstractModel):
    _name = "external.id.mixin"
    _description = "External ID Mixin"

    def get_external_system_id(self, system_code: str) -> str | None:
        self.ensure_one()
        ExternalId = self.env["external.id"]
        System = self.env["external.system"]
        system = System.search([("code", "=", system_code)], limit=1)
        if not system:
            return None
        rec = ExternalId.search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("system_id", "=", system.id),
                ("active", "=", True),
            ],
            limit=1,
        )
        return rec.external_id if rec else None

    def set_external_id(self, system_code: str, external_id_value: str) -> bool:
        self.ensure_one()
        ExternalId = self.env["external.id"]
        System = self.env["external.system"]

        system = System.search([("code", "=", system_code)], limit=1)
        if not system:
            raise ValueError(f"External system with code '{system_code}' not found")

        sanitized = (external_id_value or "").strip()

        existing = ExternalId.search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("system_id", "=", system.id),
            ],
            limit=1,
        )

        if existing:
            existing.write({"external_id": sanitized, "active": True})
        else:
            ExternalId.create(
                {
                    "res_model": self._name,
                    "res_id": self.id,
                    "system_id": system.id,
                    "external_id": sanitized,
                    "active": True,
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
                "default_reference": f"{self._name},{self.id}",
            },
        }

    # URL helpers ----------------------------------------------------------
    def _extract_numeric_id(self, external_id_value: str) -> str:
        # Convert GraphQL-style GIDs like gid://shopify/Product/123456 to 123456
        import re

        m = re.search(r"/(\d+)$", external_id_value or "")
        return m.group(1) if m else (external_id_value or "")

    def get_external_url(self, system_code: str, kind: str = "store") -> str | None:
        self.ensure_one()
        System = self.env["external.system"]
        SystemUrl = self.env["external.system.url"]

        system = System.search([("code", "=", system_code)], limit=1)
        if not system:
            return None
        # Prefer dynamic templates; fallback to legacy fields
        template = None
        urls = SystemUrl.search(
            [
                ("system_id", "=", system.id),
                ("code", "=", kind),
                ("active", "=", True),
                "|",
                ("res_model_id", "=", False),
                ("res_model_id.model", "=", self._name),
            ],
            order="res_model_id desc, sequence, id",
            limit=1,
        )
        if urls:
            template = urls.template
        elif kind in {"store", "admin"}:  # legacy compatibility
            field_name = "store_url_template" if kind == "store" else "admin_url_template"
            template = getattr(system, field_name)
        if not template:
            return None

        ext_id = self.get_external_system_id(system_code)
        if not ext_id:
            return None

        tokens = {
            "id": self._extract_numeric_id(ext_id),
            "gid": ext_id,
            "model": self._name,
            "name": self.display_name,
            "code": system.code,
            "base": system.url or "",
        }
        try:
            return template.format(**tokens)
        except Exception:
            return None

    def action_open_external_url(self) -> "odoo.values.ir_actions_act_url | odoo.values.ir_actions_client":
        self.ensure_one()
        system_code = (self.env.context or {}).get("external_system_code")
        kind = (self.env.context or {}).get("external_url_kind", "store")
        url = self.get_external_url(system_code, kind)
        if not url:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "External Link",
                    "message": "No configured URL or missing external ID.",
                    "type": "warning",
                },
            }
        return {"type": "ir.actions.act_url", "url": url, "target": "new"}
