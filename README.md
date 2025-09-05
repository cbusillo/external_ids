# External IDs Management

Manage multiple external system IDs for employees, partners, and products. Provides a reusable mixin and a central
registry model.

## Features

- Reusable mixin `external.id.mixin` for any model
- Central model `external.id` with display, validation, and linking
- Search helper: supports queries like "System: 1234" or raw IDs
- Quick actions: in‑line Sync button updates `last_sync`
- Safe deletes: active IDs must be archived before unlink
- Multi‑company: `company_id` derives from referenced record

## Security & Access

- Visibility is role‑ and company‑scoped:
    - HR users: `hr.employee` external IDs (their companies)
    - Partner Managers: `res.partner` external IDs (their companies)
    - Product Managers: `product.product` external IDs (their companies)
    - Administrators: full access
- Additional guard: reading an external ID requires read access to the referenced record.

## Models

- `external.system`: Name/code, optional URL, ID format regex, display prefix
- `external.id`:
    - Links to a record via (`res_model`, `res_id`) and `reference` helper
    - SQL constraints prevent duplicates per system and per record
    - Stored `company_id` computed from the referenced record

## Mixin API (`external.id.mixin`)

- `get_external_system_id(system_code: str) -> str | None`
- `set_external_id(system_code: str, external_id_value: str) -> bool`
- `search_by_external_id(system_code: str, external_id_value: str) -> recordset`
- `action_view_external_ids() -> ir.actions.act_window`

## Registry Helper

- `external.id.get_record_by_external_id(system_code: str, external_id: str)` returns the linked record or `None`.

## UI

- Tabs are added on Employee, Partner, and Product forms for authorized groups only.
- Dedicated menu under “External IDs” for system config and all IDs.

## Usage Tips

- Store expected formats in `external.system.id_format` (regex) for validation
- Use prefixes for nicer display, e.g., `gid://shopify/Customer/`
- Archive instead of delete for audit and safety

## Testing

- Unit tests cover constraints, compute/inverse, search helpers, and security scoping.
