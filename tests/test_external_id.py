from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestExternalId(TransactionCase):
    def setUp(self):
        super().setUp()
        self.ExternalId = self.env["external.id"]
        self.ExternalSystem = self.env["external.system"]

        # Create test systems
        self.discord_system = self.ExternalSystem.create(
            {
                "name": "Discord",
                "code": "discord",
                "id_format": r"^\d+$",  # Only digits
            }
        )

        self.shopify_system = self.ExternalSystem.create(
            {
                "name": "Shopify",
                "code": "shopify",
                "id_prefix": "gid://shopify/",
            }
        )

        # Create test records
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Customer",
                "email": "test@example.com",
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
                "default_code": "TEST001",
            }
        )

    def test_create_external_id(self):
        """Test creating an external ID"""
        external_id = self.ExternalId.create(
            {
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "system_id": self.discord_system.id,
                "external_id": "123456789",
            }
        )

        self.assertEqual(external_id.res_model, "res.partner")
        self.assertEqual(external_id.res_id, self.partner.id)
        self.assertEqual(external_id.external_id, "123456789")
        self.assertTrue(external_id.active)

    def test_reference_field(self):
        """Test the reference field computation"""
        external_id = self.ExternalId.create(
            {
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "system_id": self.shopify_system.id,
                "external_id": "Customer/123",
            }
        )

        self.assertEqual(external_id.reference, self.partner)
        self.assertEqual(external_id.record_name, "Test Customer")

    def test_display_name_computation(self):
        """Test display name with and without prefix"""
        # Without prefix
        external_id = self.ExternalId.create(
            {
                "res_model": "hr.employee",
                "res_id": self.employee.id,
                "system_id": self.discord_system.id,
                "external_id": "987654321",
            }
        )

        self.assertIn("Discord", external_id.display_name)
        self.assertIn("987654321", external_id.display_name)
        self.assertIn("Test Employee", external_id.display_name)

        # With prefix
        external_id2 = self.ExternalId.create(
            {
                "res_model": "product.product",
                "res_id": self.product.id,
                "system_id": self.shopify_system.id,
                "external_id": "Product/456",
            }
        )

        self.assertIn("gid://shopify/", external_id2.display_name)

    def test_id_format_validation(self):
        """Test that external IDs must match the system's format"""
        with self.assertRaises(ValidationError):
            self.ExternalId.create(
                {
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                    "system_id": self.discord_system.id,
                    "external_id": "ABC123",  # Contains letters, format requires only digits
                }
            )

    def test_unique_record_per_system(self):
        """Test that each record can only have one ID per system"""
        self.ExternalId.create(
            {
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "system_id": self.discord_system.id,
                "external_id": "111111111",
            }
        )

        with self.assertRaises(ValidationError):
            self.ExternalId.create(
                {
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                    "system_id": self.discord_system.id,
                    "external_id": "222222222",
                }
            )

    def test_unique_external_id_per_system(self):
        """Test that external IDs must be unique within a system"""
        self.ExternalId.create(
            {
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "system_id": self.shopify_system.id,
                "external_id": "UNIQUE123",
            }
        )

        partner2 = self.env["res.partner"].create({"name": "Another Partner"})

        with self.assertRaises(ValidationError):
            self.ExternalId.create(
                {
                    "res_model": "res.partner",
                    "res_id": partner2.id,
                    "system_id": self.shopify_system.id,
                    "external_id": "UNIQUE123",
                }
            )

    def test_action_sync(self):
        """Test the sync action"""
        external_id = self.ExternalId.create(
            {
                "res_model": "product.product",
                "res_id": self.product.id,
                "system_id": self.shopify_system.id,
                "external_id": "Product/789",
            }
        )

        self.assertFalse(external_id.last_sync)

        result = external_id.action_sync()

        self.assertTrue(external_id.last_sync)
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")

    def test_get_record_by_external_id(self):
        """Test finding records by external ID"""
        self.ExternalId.create(
            {
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "system_id": self.discord_system.id,
                "external_id": "555555555",
            }
        )

        # Find existing record
        found_record = self.ExternalId.get_record_by_external_id("discord", "555555555")
        self.assertEqual(found_record, self.partner)

        # Non-existent external ID
        not_found = self.ExternalId.get_record_by_external_id("discord", "999999999")
        self.assertFalse(not_found)

        # Non-existent system
        not_found2 = self.ExternalId.get_record_by_external_id("nonexistent", "555555555")
        self.assertFalse(not_found2)

    def test_inactive_external_id(self):
        """Test that inactive external IDs are not found in searches"""
        self.ExternalId.create(
            {
                "res_model": "hr.employee",
                "res_id": self.employee.id,
                "system_id": self.discord_system.id,
                "external_id": "777777777",
                "active": False,
            }
        )

        # Should not be found when searching for active records
        found = self.ExternalId.get_record_by_external_id("discord", "777777777")
        self.assertFalse(found)

    def test_deleted_record_handling(self):
        """Test handling of deleted referenced records"""
        external_id = self.ExternalId.create(
            {
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "system_id": self.discord_system.id,
                "external_id": "888888888",
            }
        )

        # Delete the partner
        self.partner.unlink()

        # Compute record name should handle deleted records
        external_id._compute_record_name()
        self.assertIn("Deleted", external_id.record_name)

    def test_prevent_active_deletion(self):
        """Test that active external IDs cannot be deleted"""
        external_id = self.ExternalId.create(
            {
                "res_model": "product.product",
                "res_id": self.product.id,
                "system_id": self.shopify_system.id,
                "external_id": "Product/999",
                "active": True,
            }
        )

        with self.assertRaises(ValidationError):
            external_id.unlink()

        # Should work after archiving
        external_id.active = False
        external_id.unlink()  # Should not raise
