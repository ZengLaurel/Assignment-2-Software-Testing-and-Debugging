"""
Unit tests for Problem 3: Order

Instructions:
Complete the unit test methods below using Python's unittest framework.
Your test methods must assert MULTIPLE ATTRIBUTES on the Order object
(e.g., subtotal, discount_amount, tax_amount, shipping_fee, final_total, status)
to verify state consistency under various conditions.

Running tests:
    python -m unittest test_problem3.py -v
"""
import unittest
from problem3 import Order


class TestOrder(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.regular_order = Order("order001", customer_tier="regular")
        self.silver_order = Order("order002", customer_tier="silver")
        self.gold_order = Order("order003", customer_tier="gold")

    def test_initial_state_multi_attributes(self):
        """Verify all attributes are correctly initialised for each tier."""
        for order, oid, tier in [
            (self.regular_order, "order001", "regular"),
            (self.silver_order,  "order002", "silver"),
            (self.gold_order,    "order003", "gold"),
        ]:
            self.assertEqual(order.order_id, oid)
            self.assertEqual(order.customer_tier, tier)
            self.assertEqual(order.status, "PENDING")
            self.assertIsNone(order.applied_coupon)
            self.assertEqual(order.items, {})
            self.assertEqual(order.subtotal, 0.0)
            self.assertEqual(order.discount_amount, 0.0)
            self.assertEqual(order.tax_amount, 0.0)
            self.assertEqual(order.shipping_fee, 0.0)
            self.assertEqual(order.final_total, 0.0)

        # Tier input is case-insensitive
        mixed = Order("order004", customer_tier="Silver")
        self.assertEqual(mixed.customer_tier, "silver")

        # get_summary() reflects initial state
        s = self.regular_order.get_summary()
        self.assertEqual(s["order_id"], "order001")
        self.assertEqual(s["tier"], "regular")
        self.assertEqual(s["status"], "PENDING")
        self.assertEqual(s["item_count"], 0)
        self.assertEqual(s["subtotal"], 0.0)

        # Invalid tier raises ValueError
        with self.assertRaises(ValueError):
            Order("ord-invalid-99", customer_tier="platinum")

    def test_add_item_updates_multiple_attributes(self):
        """Adding items must update items dict, subtotal, tax, shipping, and final_total."""
        # Add item at $45.60 qty 2 → subtotal 91.20, net 91.20, tax 7.3, ship 0.0 (≥50), final 98.5
        self.regular_order.add_item("laptop", 45.60, 2, "general")

        item = self.regular_order.items["laptop"]
        self.assertEqual(item["price"], 45.60)
        self.assertEqual(item["quantity"], 2)
        self.assertEqual(item["category"], "general")

        self.assertEqual(self.regular_order.subtotal, 91.20)
        self.assertEqual(self.regular_order.discount_amount, 0.0)
        self.assertEqual(self.regular_order.tax_amount, 7.30)
        self.assertEqual(self.regular_order.shipping_fee, 0.0)
        self.assertEqual(self.regular_order.final_total, 98.50)
        self.assertEqual(self.regular_order.status, "PENDING")

        s = self.regular_order.get_summary()
        self.assertEqual(s["item_count"], 2)
        self.assertEqual(s["final_total"], 98.50)

        # Duplicate name increments quantity (add 1 more → qty 3)
        self.regular_order.add_item("laptop", 45.60, 1)
        self.assertEqual(self.regular_order.items["laptop"]["quantity"], 3)
        self.assertEqual(self.regular_order.subtotal, 136.80)

        # Invalid price / quantity raise ValueError
        with self.assertRaises(ValueError):
            self.regular_order.add_item("invalid", 0, 1)
        with self.assertRaises(ValueError):
            self.regular_order.add_item("invalid", 10.0, 0)

    def test_tier_discounts_multi_attributes(self):
        """Tier discount must lower discount_amount, tax, and final_total proportionally."""
        # Item: $12.00 qty 3 → subtotal $36.00 each
        for order in (self.regular_order, self.silver_order, self.gold_order):
            order.add_item("pen", 12.0, 3, "general")

        self.assertEqual(self.regular_order.subtotal, 36.0)
        self.assertEqual(self.silver_order.subtotal, 36.0)
        self.assertEqual(self.gold_order.subtotal, 36.0)

        # Discount increases with tier
        self.assertEqual(self.regular_order.discount_amount, 0.0)
        self.assertEqual(self.silver_order.discount_amount, 1.8)     # 36 * 5%
        self.assertEqual(self.gold_order.discount_amount, 3.6)       # 36 * 10%

        # Tax base shrinks with higher tier
        self.assertEqual(self.regular_order.tax_amount, 2.88)        # 36 * 0.08
        self.assertEqual(self.silver_order.tax_amount, 2.74)         # round(34.2*0.08, 2)
        self.assertEqual(self.gold_order.tax_amount, 2.59)           # round(32.4*0.08, 2)

        # Shipping: all nets < 50 → 5.99
        self.assertEqual(self.regular_order.shipping_fee, 5.99)
        self.assertEqual(self.silver_order.shipping_fee, 5.99)
        self.assertEqual(self.gold_order.shipping_fee, 5.99)

        # Final total
        self.assertEqual(self.regular_order.final_total, 44.87)
        self.assertEqual(self.silver_order.final_total, 42.93)
        self.assertEqual(self.gold_order.final_total, 40.98)

    def test_coupon_discounts_multi_attributes(self):
        """Coupons must stack on top of tier discounts and be case-insensitive."""
        # SAVE10 on regular: $25.00 qty 2 → subtotal 50, coupon = 5.0, net 45, tax 3.6, ship 5.99, final 54.59
        self.regular_order.add_item("keyboard", 25.0, 2, "general")
        self.regular_order.apply_coupon("save10")
        self.assertEqual(self.regular_order.applied_coupon, "SAVE10")
        self.assertEqual(self.regular_order.discount_amount, 5.0)
        self.assertEqual(self.regular_order.tax_amount, 3.6)
        self.assertEqual(self.regular_order.final_total, 54.59)

        # FLAT15 on fresh order: $40.00 qty 2 → subtotal 80, coupon 15, net 65, tax 5.2, ship 0, final 70.2
        flat_order = Order("order-flat-123", customer_tier="regular")
        flat_order.add_item("monitor", 40.0, 2, "general")
        flat_order.apply_coupon("FLAT15")
        self.assertEqual(flat_order.discount_amount, 15.0)
        self.assertEqual(flat_order.final_total, 70.2)

        # FLAT15 capped: $8.00 qty 1 → subtotal 8, coupon 8, net 0, tax 0, ship 5.99, final 5.99
        small = Order("order-flat-456", customer_tier="regular")
        small.add_item("pen", 8.0, 1, "general")
        small.apply_coupon("FLAT15")
        self.assertEqual(small.discount_amount, 8.0)
        self.assertEqual(small.final_total, 5.99)

        # gold+SAVE10: $25.00 qty 2 → subtotal 50, tier 5, remaining 45, coupon 4.5, disc 9.5, net 40.5, tax 3.24, ship 5.99, final 49.73
        self.gold_order.add_item("keyboard", 25.0, 2, "general")
        self.gold_order.apply_coupon("SAVE10")
        self.assertEqual(self.gold_order.discount_amount, 9.5)
        self.assertEqual(self.gold_order.final_total, 49.73)

        # Invalid coupon raises ValueError
        with self.assertRaises(ValueError):
            self.silver_order.apply_coupon("BADCODE")

    def test_tax_and_shipping_multi_attributes(self):
        """Grocery items must be tax-exempt; shipping waived when net subtotal >= $50."""
        # All grocery: $12.00 qty 1 → tax 0, ship 5.99, final 17.99
        grocery = Order("order-groc-123", customer_tier="regular")
        grocery.add_item("milk", 12.0, 1, "grocery")
        self.assertEqual(grocery.tax_amount, 0.0)
        self.assertEqual(grocery.shipping_fee, 5.99)
        self.assertEqual(grocery.final_total, 17.99)

        # Net >= 50 → free shipping: $60.00 qty 1
        free = Order("order-elec-456", customer_tier="regular")
        free.add_item("desk", 60.0, 1, "general")
        self.assertEqual(free.shipping_fee, 0.0)
        self.assertEqual(free.tax_amount, 4.8)
        self.assertEqual(free.final_total, 64.8)

        # Net < 50 → shipping charged: $49.00 qty 1
        below = Order("order-elec-789", customer_tier="regular")
        below.add_item("chair", 49.0, 1, "general")
        self.assertEqual(below.shipping_fee, 5.99)

        # Mixed grocery + general: $15.00 (general) + $40.00 (grocery) = $55.00
        # tax only on general: 15 * 0.08 = 1.2, ship 0, final 56.2
        mixed = Order("order-mix-999", customer_tier="regular")
        mixed.add_item("bread", 40.0, 1, "grocery")
        mixed.add_item("book", 15.0, 1, "general")
        self.assertEqual(mixed.subtotal, 55.0)
        self.assertEqual(mixed.tax_amount, 1.2)
        self.assertEqual(mixed.shipping_fee, 0.0)
        self.assertEqual(mixed.final_total, 56.2)

    def test_remove_item_multi_attributes(self):
        """Removing items must correctly update all monetary attributes."""
        # Add keyboard $35.00 qty 3 → subtotal 105
        self.regular_order.add_item("keyboard", 35.0, 3, "general")

        # Decrease quantity by 2 → qty 1, subtotal 35
        self.regular_order.remove_item("keyboard", 2)
        self.assertEqual(self.regular_order.items["keyboard"]["quantity"], 1)
        self.assertEqual(self.regular_order.subtotal, 35.0)

        # Remove entirely (quantity=None)
        self.regular_order.remove_item("keyboard")
        self.assertNotIn("keyboard", self.regular_order.items)
        self.assertEqual(self.regular_order.subtotal, 0.0)
        self.assertEqual(self.regular_order.final_total, 0.0)

        # KeyError for missing item
        with self.assertRaises(KeyError):
            self.regular_order.remove_item("nonexistent")

        # ValueError for zero / negative remove quantity
        self.regular_order.add_item("mouse", 12.0, 2, "general")
        with self.assertRaises(ValueError):
            self.regular_order.remove_item("mouse", 0)
        with self.assertRaises(ValueError):
            self.regular_order.remove_item("mouse", -1)

    def test_checkout_cancel_status_transitions(self):
        """Status transitions and post-transition operation restrictions."""
        # Empty order cannot be checked out
        with self.assertRaises(ValueError):
            self.regular_order.checkout()

        # Successful checkout transitions to PAID: desk_lamp $34.95 x1
        self.regular_order.add_item("desk_lamp", 34.95, 1, "general")
        result = self.regular_order.checkout()
        self.assertTrue(result)
        self.assertEqual(self.regular_order.status, "PAID")

        # PAID order rejects all modifications
        with self.assertRaises(RuntimeError):
            self.regular_order.add_item("extra_bulb", 4.99, 1)
        with self.assertRaises(RuntimeError):
            self.regular_order.remove_item("desk_lamp")
        with self.assertRaises(RuntimeError):
            self.regular_order.apply_coupon("SAVE10")

        # Cannot cancel a PAID order
        with self.assertRaises(RuntimeError):
            self.regular_order.cancel()

        # Cancel a PENDING order
        result = self.silver_order.cancel()
        self.assertTrue(result)
        self.assertEqual(self.silver_order.status, "CANCELLED")

        # CANCELLED order rejects modifications too
        with self.assertRaises(RuntimeError):
            self.silver_order.add_item("stapler", 7.25, 1)




if __name__ == "__main__":
    unittest.main()
