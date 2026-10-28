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
        # Add ("wireless_mouse", $17.99, qty 3, "general"):
        # subtotal = 17.99 * 3 = 53.97, net 53.97, tax = round(53.97*0.08,2) = 4.32, ship 0.0 (>=50), final 58.29
        self.regular_order.add_item("wireless_mouse", 17.99, 3, "general")

        item = self.regular_order.items["wireless_mouse"]
        self.assertEqual(item["price"], 17.99)
        self.assertEqual(item["quantity"], 3)
        self.assertEqual(item["category"], "general")

        self.assertEqual(self.regular_order.subtotal, 53.97)
        self.assertEqual(self.regular_order.discount_amount, 0.0)
        self.assertEqual(self.regular_order.tax_amount, 4.32)
        self.assertEqual(self.regular_order.shipping_fee, 0.0)
        self.assertEqual(self.regular_order.final_total, 58.29)
        self.assertEqual(self.regular_order.status, "PENDING")

        s = self.regular_order.get_summary()
        self.assertEqual(s["item_count"], 3)
        self.assertEqual(s["final_total"], 58.29)

        # Duplicate name increments quantity (add 2 more → qty 5, subtotal 89.95)
        self.regular_order.add_item("wireless_mouse", 17.99, 2)
        self.assertEqual(self.regular_order.items["wireless_mouse"]["quantity"], 5)
        self.assertEqual(self.regular_order.subtotal, 89.95)

        # Invalid price / quantity raise ValueError
        with self.assertRaises(ValueError):
            self.regular_order.add_item("broken", 0, 1)
        with self.assertRaises(ValueError):
            self.regular_order.add_item("broken", 9.99, 0)

    def test_tier_discounts_multi_attributes(self):
        """Tier discount must lower discount_amount, tax, and final_total proportionally."""
        # Same item on all three orders: price $13.50, qty 3 → subtotal 40.50 each
        for order in (self.regular_order, self.silver_order, self.gold_order):
            order.add_item("usb_hub", 13.50, 3, "general")

        self.assertEqual(self.regular_order.subtotal, 40.5)
        self.assertEqual(self.silver_order.subtotal, 40.5)
        self.assertEqual(self.gold_order.subtotal, 40.5)

        # Discount increases with tier
        self.assertEqual(self.regular_order.discount_amount, 0.0)
        self.assertEqual(self.silver_order.discount_amount, 2.02)   # round(40.5*0.05, 2)
        self.assertEqual(self.gold_order.discount_amount, 4.05)     # round(40.5*0.10, 2)

        # Tax base shrinks with higher tier (net * 0.08)
        self.assertEqual(self.regular_order.tax_amount, 3.24)       # 40.5 * 0.08
        self.assertEqual(self.silver_order.tax_amount, 3.08)        # 38.48 * 0.08
        self.assertEqual(self.gold_order.tax_amount, 2.92)          # 36.45 * 0.08

        # Shipping: all nets < 50 → 5.99
        self.assertEqual(self.regular_order.shipping_fee, 5.99)
        self.assertEqual(self.silver_order.shipping_fee, 5.99)
        self.assertEqual(self.gold_order.shipping_fee, 5.99)

        # Final total
        self.assertEqual(self.regular_order.final_total, 49.73)
        self.assertEqual(self.silver_order.final_total, 47.55)
        self.assertEqual(self.gold_order.final_total, 45.36)

    def test_coupon_discounts_multi_attributes(self):
        """Coupons must stack on top of tier discounts and be case-insensitive."""
        # SAVE10 on regular: price $14.75 qty 3 → subtotal 44.25
        # coupon = 44.25 * 0.10 = 4.43, net 39.82, tax = round(39.82*0.08,2) = 3.19, ship 5.99, final 49.0
        self.regular_order.add_item("keyboard", 14.75, 3, "general")
        self.regular_order.apply_coupon("save10")   # lowercase accepted
        self.assertEqual(self.regular_order.applied_coupon, "SAVE10")
        self.assertEqual(self.regular_order.discount_amount, 4.42)
        self.assertEqual(self.regular_order.tax_amount, 3.19)
        self.assertEqual(self.regular_order.final_total, 49.01)

        # FLAT15 on a fresh regular order: price $11.30 qty 4 → subtotal 45.20
        # coupon = min(15, 45.20) = 15, net 30.20, tax = round(30.20*0.08,2) = 2.42, ship 5.99, final 38.61
        flat_order = Order("order-flat-1", customer_tier="regular")
        flat_order.add_item("hdmi_cable", 11.30, 4, "general")
        flat_order.apply_coupon("FLAT15")
        self.assertEqual(flat_order.discount_amount, 15.0)
        self.assertEqual(flat_order.tax_amount, 2.42)
        self.assertEqual(flat_order.final_total, 38.61)

        # FLAT15 is capped when remaining subtotal < 15: price $6.49 qty 1 → subtotal 6.49
        # coupon = min(15, 6.49) = 6.49, net 0, tax 0, ship 5.99, final 5.99
        small = Order("order-flat-2", customer_tier="regular")
        small.add_item("stylus", 6.49, 1, "general")
        small.apply_coupon("FLAT15")
        self.assertEqual(small.discount_amount, 6.49)
        self.assertEqual(small.tax_amount, 0.0)
        self.assertEqual(small.final_total, 5.99)

        # SAVE10 stacks with gold tier: price $14.75 qty 3 → subtotal 44.25
        # tier = round(44.25*0.10,2) = 4.43, remaining = 39.82, coupon = round(39.82*0.10,2) = 3.98
        # disc = 8.41, net = 35.84, tax = round(35.84*0.08,2) = 2.87, ship 5.99, final 44.7
        self.gold_order.add_item("keyboard", 14.75, 3, "general")
        self.gold_order.apply_coupon("SAVE10")
        self.assertEqual(self.gold_order.discount_amount, 8.41)
        self.assertEqual(self.gold_order.final_total, 44.7)

        # Invalid coupon raises ValueError
        with self.assertRaises(ValueError):
            self.silver_order.apply_coupon("WEEKEND20")

    def test_tax_and_shipping_multi_attributes(self):
        """Grocery items must be tax-exempt; shipping waived when net subtotal >= $50."""
        # All grocery → tax 0: orange_juice $8.49 x1
        grocery = Order("order-groc-1", customer_tier="regular")
        grocery.add_item("orange_juice", 8.49, 1, "grocery")
        self.assertEqual(grocery.tax_amount, 0.0)
        self.assertEqual(grocery.shipping_fee, 5.99)    # net 8.49 < 50
        self.assertEqual(grocery.final_total, 14.48)

        # Net >= 50 → free shipping: monitor_stand $53.50 x1
        free = Order("order-elec-7", customer_tier="regular")
        free.add_item("monitor_stand", 53.50, 1, "general")
        self.assertEqual(free.shipping_fee, 0.0)
        self.assertEqual(free.tax_amount, 4.28)         # round(53.50*0.08, 2)
        self.assertEqual(free.final_total, 57.78)

        # Net just below 50 → shipping charged: charger $49.99 x1
        below = Order("order-elec-8", customer_tier="regular")
        below.add_item("charger", 49.99, 1, "general")
        self.assertEqual(below.shipping_fee, 5.99)

        # Mixed grocery + general: only general portion taxed
        # notebook $37.50 x1 (general) + yoghurt $12.80 x1 (grocery) → subtotal 50.30
        # net 50.30, ratio 1.0, taxable 37.50, tax round(37.50*0.08,2)=3.0, ship 0.0, final 53.3
        mixed = Order("order-mix-3", customer_tier="regular")
        mixed.add_item("yoghurt", 12.80, 1, "grocery")
        mixed.add_item("notebook", 37.50, 1, "general")
        self.assertEqual(mixed.subtotal, 50.3)
        self.assertEqual(mixed.tax_amount, 3.0)
        self.assertEqual(mixed.shipping_fee, 0.0)
        self.assertEqual(mixed.final_total, 53.3)

    def test_remove_item_multi_attributes(self):
        """Removing items must correctly update all monetary attributes."""
        # Add webcam $23.99 x4 → subtotal 95.96
        self.regular_order.add_item("webcam", 23.99, 4, "general")

        # Decrease quantity by 3 → qty becomes 1, subtotal 23.99
        self.regular_order.remove_item("webcam", 3)
        self.assertEqual(self.regular_order.items["webcam"]["quantity"], 1)
        self.assertEqual(self.regular_order.subtotal, 23.99)

        # Remove remaining entirely (quantity=None removes the whole entry)
        self.regular_order.remove_item("webcam")
        self.assertNotIn("webcam", self.regular_order.items)
        self.assertEqual(self.regular_order.subtotal, 0.0)
        self.assertEqual(self.regular_order.final_total, 0.0)

        # KeyError for missing item
        with self.assertRaises(KeyError):
            self.regular_order.remove_item("phantom_item")

        # ValueError for zero / negative remove quantity
        self.regular_order.add_item("mousepad", 12.50, 3, "general")
        with self.assertRaises(ValueError):
            self.regular_order.remove_item("mousepad", 0)
        with self.assertRaises(ValueError):
            self.regular_order.remove_item("mousepad", -2)

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
