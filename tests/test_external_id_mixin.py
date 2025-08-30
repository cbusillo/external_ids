from odoo.tests import TransactionCase


class TestExternalIdMixin(TransactionCase):
    def setUp(self):
        super().setUp()
        self.ExternalSystem = self.env["external.system"]
        self.ExternalId = self.env["external.id"]

        # Create test systems
        self.discord = self.ExternalSystem.create(
            {
                "name": "Discord",
                "code": "discord",
            }
        )

        self.shopify = self.ExternalSystem.create(
            {
                "name": "Shopify",
                "code": "shopify",
            }
        )

        # Create test records with mixin
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test Employee",
            }
        )

        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "default_code": "PROD001",
            }
        )

    def test_external_ids_computed_field(self):
        """Test that external_ids field is computed correctly"""
        # Initially no external IDs
        self.assertEqual(len(self.partner.external_ids), 0)

        # Create an external ID
        external_id = self.ExternalId.create(
            {
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "system_id": self.discord.id,
                "external_id": "PARTNER123",
            }
        )

        # Recompute and check
        self.partner._compute_external_ids()
        self.assertEqual(len(self.partner.external_ids), 1)
        self.assertEqual(self.partner.external_ids[0], external_id)

    def test_get_external_system_id(self):
        """Test getting an external ID for a specific system"""
        # Set an external ID
        self.ExternalId.create(
            {
                "res_model": "hr.employee",
                "res_id": self.employee.id,
                "system_id": self.discord.id,
                "external_id": "EMP456",
            }
        )

        # Get the external ID
        discord_id = self.employee.get_external_system_id("discord")
        self.assertEqual(discord_id, "EMP456")

        # Non-existent system
        shopify_id = self.employee.get_external_system_id("shopify")
        self.assertFalse(shopify_id)

    def test_set_external_id(self):
        """Test setting an external ID for a record"""
        # Set a new external ID
        self.product.set_external_id("shopify", "SHOP789")

        # Verify it was created
        external_id = self.ExternalId.search(
            [
                ("res_model", "=", "product.product"),
                ("res_id", "=", self.product.id),
                ("system_id", "=", self.shopify.id),
            ]
        )

        self.assertTrue(external_id)
        self.assertEqual(external_id.external_id, "SHOP789")

        # Update existing external ID
        self.product.set_external_id("shopify", "SHOP999")

        # Should update, not create duplicate
        external_ids = self.ExternalId.search(
            [
                ("res_model", "=", "product.product"),
                ("res_id", "=", self.product.id),
                ("system_id", "=", self.shopify.id),
            ]
        )

        self.assertEqual(len(external_ids), 1)
        self.assertEqual(external_ids.external_id, "SHOP999")

    def test_set_external_id_invalid_system(self):
        """Test setting external ID with invalid system code"""
        with self.assertRaises(ValueError):
            self.partner.set_external_id("nonexistent", "ID123")

    def test_search_by_external_id(self):
        """Test searching for records by external ID"""
        # Create multiple partners with external IDs
        partner1 = self.env["res.partner"].create({"name": "Partner 1"})
        partner2 = self.env["res.partner"].create({"name": "Partner 2"})

        self.ExternalId.create(
            {
                "res_model": "res.partner",
                "res_id": partner1.id,
                "system_id": self.discord.id,
                "external_id": "DISC001",
            }
        )

        self.ExternalId.create(
            {
                "res_model": "res.partner",
                "res_id": partner2.id,
                "system_id": self.discord.id,
                "external_id": "DISC002",
            }
        )

        # Search for partner by external ID
        found = self.env["res.partner"].search_by_external_id("discord", "DISC001")
        self.assertEqual(found, partner1)

        # Search for non-existent ID
        not_found = self.env["res.partner"].search_by_external_id("discord", "DISC999")
        self.assertFalse(not_found)

        # Search with non-existent system
        not_found2 = self.env["res.partner"].search_by_external_id("invalid", "DISC001")
        self.assertFalse(not_found2)

    def test_action_view_external_ids(self):
        """Test the action to view external IDs for a record"""
        # Create some external IDs
        self.ExternalId.create(
            {
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "system_id": self.discord.id,
                "external_id": "DISC123",
            }
        )

        self.ExternalId.create(
            {
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "system_id": self.shopify.id,
                "external_id": "SHOP456",
            }
        )

        # Get the action
        action = self.partner.action_view_external_ids()

        self.assertEqual(action["res_model"], "external.id")
        self.assertEqual(action["domain"], [("res_model", "=", "res.partner"), ("res_id", "=", self.partner.id)])
        self.assertIn("External IDs for", action["name"])

    def test_multiple_models_with_mixin(self):
        """Test that multiple models can use the mixin independently"""
        # Set external IDs for different models
        self.partner.set_external_id("discord", "PARTNER_DISC")
        self.employee.set_external_id("discord", "EMPLOYEE_DISC")
        self.product.set_external_id("discord", "PRODUCT_DISC")

        # Each should have their own external ID
        self.assertEqual(self.partner.get_external_system_id("discord"), "PARTNER_DISC")
        self.assertEqual(self.employee.get_external_system_id("discord"), "EMPLOYEE_DISC")
        self.assertEqual(self.product.get_external_system_id("discord"), "PRODUCT_DISC")

        # Search should find the right record
        found_partner = self.env["res.partner"].search_by_external_id("discord", "PARTNER_DISC")
        found_employee = self.env["hr.employee"].search_by_external_id("discord", "EMPLOYEE_DISC")
        found_product = self.env["product.product"].search_by_external_id("discord", "PRODUCT_DISC")

        self.assertEqual(found_partner, self.partner)
        self.assertEqual(found_employee, self.employee)
        self.assertEqual(found_product, self.product)

    def test_inactive_external_ids_not_returned(self):
        """Test that inactive external IDs are not returned by get_external_system_id"""
        # Create an inactive external ID
        self.ExternalId.create(
            {
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "system_id": self.discord.id,
                "external_id": "INACTIVE123",
                "active": False,
            }
        )

        # Should not be returned
        discord_id = self.partner.get_external_system_id("discord")
        self.assertFalse(discord_id)
