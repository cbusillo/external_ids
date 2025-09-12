{
    "name": "External IDs Management",
    "version": "18.0.1.0.1",
    "category": "Technical",
    "summary": "Manage multiple external system IDs for employees, partners, and products.",
    "description": """
        Manage external systems and assign/manage multiple external IDs per record.
    """,
    "author": "Chris Busillo (Shiny Computers)",
    "maintainers": ["cbusillo"],
    "development_status": "Beta",
    "license": "LGPL-3",
    "depends": ["hr", "base", "product"],
    "data": [
        "security/ir.model.access.csv",
        "views/menu_views.xml",
        "views/external_system_views.xml",
        "views/external_id_views.xml",
        "views/external_system_url_views.xml",
        "views/hr_employee_views.xml",
        "views/res_partner_views.xml",
        "views/product_template_views.xml",
    ],
    "installable": True,
    "application": False,
}
