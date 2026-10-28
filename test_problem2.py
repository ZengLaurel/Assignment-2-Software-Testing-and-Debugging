"""
Unit tests for Problem 2: BankAccount

Instructions:
Complete the unit test methods below using Python's unittest framework.
Your test methods must assert MULTIPLE ATTRIBUTES on the BankAccount object
(e.g., balance, status, transaction_history, summary) to verify state consistency.

Running tests:
    python -m unittest test_problem2.py -v
"""
import unittest
from problem2 import BankAccount


class TestBankAccount(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.account_empty = BankAccount("ACC001", "Alice", initial_balance=0.0, overdraft_limit=100.0)
        self.account_funded = BankAccount("ACC002", "Bob", initial_balance=200.0, overdraft_limit=50.0)

    def test_initial_state_multi_attributes(self):
        """
        Verify that a newly created account initializes all attributes correctly.
        Check balance, owner, status, overdraft_limit, transaction_history, and summary.
        """
        # Test empty account
        self.assertEqual(self.account_empty.account_id, "ACC001")
        self.assertEqual(self.account_empty.owner, "Alice")
        self.assertEqual(self.account_empty.balance, 0.0)
        self.assertEqual(self.account_empty.status, "ACTIVE")
        self.assertEqual(self.account_empty.overdraft_limit, 100.0)
        self.assertEqual(len(self.account_empty.transaction_history), 0)

        # Test get_summary() for empty account
        summary_empty = self.account_empty.get_summary()
        self.assertEqual(summary_empty["account_id"], "ACC001")
        self.assertEqual(summary_empty["owner"], "Alice")
        self.assertEqual(summary_empty["balance"], 0.0)
        self.assertEqual(summary_empty["status"], "ACTIVE")
        self.assertEqual(summary_empty["overdraft_limit"], 100.0)
        self.assertEqual(summary_empty["transaction_count"], 0)

        # Test funded account
        self.assertEqual(self.account_funded.account_id, "ACC002")
        self.assertEqual(self.account_funded.owner, "Bob")
        self.assertEqual(self.account_funded.balance, 200.0)
        self.assertEqual(self.account_funded.status, "ACTIVE")
        self.assertEqual(self.account_funded.overdraft_limit, 50.0)
        self.assertEqual(len(self.account_funded.transaction_history), 1)

        # Verify the initial deposit transaction record
        initial_tx = self.account_funded.transaction_history[0]
        self.assertEqual(initial_tx["type"], "INITIAL_DEPOSIT")
        self.assertEqual(initial_tx["amount"], 200.0)
        self.assertEqual(initial_tx["fee"], 0.0)
        self.assertEqual(initial_tx["balance_after"], 200.0)

        # Test get_summary() for funded account
        summary_funded = self.account_funded.get_summary()
        self.assertEqual(summary_funded["account_id"], "ACC002")
        self.assertEqual(summary_funded["owner"], "Bob")
        self.assertEqual(summary_funded["balance"], 200.0)
        self.assertEqual(summary_funded["status"], "ACTIVE")
        self.assertEqual(summary_funded["overdraft_limit"], 50.0)
        self.assertEqual(summary_funded["transaction_count"], 1)

        pass

    def test_deposit_updates_multiple_attributes(self):
        """
        Test that deposit correctly updates balance, transaction_history, and summary.
        """
        # Deposit $150 into the empty account and capture the return value
        result = self.account_empty.deposit(150)

        # deposit() should return True on success
        self.assertTrue(result)

        # Balance should increase from 0 to 150
        self.assertEqual(self.account_empty.balance, 150.0)

        # Status should remain ACTIVE (no overdraft involved)
        self.assertEqual(self.account_empty.status, "ACTIVE")

        # Exactly one transaction record should exist
        self.assertEqual(len(self.account_empty.transaction_history), 1)

        # Verify each field of the transaction record
        tx = self.account_empty.transaction_history[0]
        self.assertEqual(tx["type"], "DEPOSIT")
        self.assertEqual(tx["amount"], 150.0)
        self.assertEqual(tx["fee"], 0.0)
        self.assertEqual(tx["balance_after"], 150.0)
        self.assertEqual(tx["description"], "Deposit of $150.00")

        # get_summary() should reflect the updated balance and transaction count
        summary = self.account_empty.get_summary()
        self.assertEqual(summary["balance"], 150.0)
        self.assertEqual(summary["transaction_count"], 1)

    def test_withdrawal_within_balance_multi_attributes(self):
        """
        Test withdrawal when sufficient positive balance exists.
        """
        # Withdraw $50 with a $2.50 fee from the funded account (balance 200)
        result = self.account_funded.withdraw(50, fee=2.50)

        # withdraw() should return True on success
        self.assertTrue(result)

        # Balance should be 200 - 50 - 2.50 = 147.50
        self.assertEqual(self.account_funded.balance, 147.50)

        # Status should remain ACTIVE (balance is still positive)
        self.assertEqual(self.account_funded.status, "ACTIVE")

        # A new withdrawal record should be appended after the initial deposit
        self.assertEqual(len(self.account_funded.transaction_history), 2)

        # Verify each field of the withdrawal record
        tx = self.account_funded.transaction_history[1]
        self.assertEqual(tx["type"], "WITHDRAWAL")
        self.assertEqual(tx["amount"], 50.0)
        self.assertEqual(tx["fee"], 2.50)
        self.assertEqual(tx["balance_after"], 147.50)
        self.assertEqual(tx["description"], "Withdrawal of $50.00 (Fee: $2.50)")

        # get_summary() should reflect the updated balance and transaction count
        summary = self.account_funded.get_summary()
        self.assertEqual(summary["balance"], 147.50)
        self.assertEqual(summary["transaction_count"], 2)

    def test_overdraft_withdrawal_and_status_transition(self):
        """
        Test withdrawal that uses overdraft protection (balance becomes negative but >= -overdraft_limit).
        """
        # Withdraw $50 from the empty account (balance 0, overdraft limit 100)
        result = self.account_empty.withdraw(50)

        # withdraw() should return True on success
        self.assertTrue(result)

        # Balance should drop to -50 (within the overdraft limit of 100)
        self.assertEqual(self.account_empty.balance, -50.0)

        # Status should transition from ACTIVE to OVERDRAWN
        self.assertEqual(self.account_empty.status, "OVERDRAWN")

        # Exactly one transaction record should exist
        self.assertEqual(len(self.account_empty.transaction_history), 1)

        # Verify each field of the transaction record
        tx = self.account_empty.transaction_history[0]
        self.assertEqual(tx["type"], "WITHDRAWAL")
        self.assertEqual(tx["amount"], 50.0)
        self.assertEqual(tx["fee"], 0.0)
        self.assertEqual(tx["balance_after"], -50.0)

        # get_summary() should reflect the negative balance, overdrawn status, and count
        summary = self.account_empty.get_summary()
        self.assertEqual(summary["balance"], -50.0)
        self.assertEqual(summary["status"], "OVERDRAWN")
        self.assertEqual(summary["transaction_count"], 1)

    def test_deposit_recovering_from_overdrawn_status(self):
        """
        Test that depositing enough money to bring balance >= 0 transitions status from OVERDRAWN to ACTIVE.
        """
        # First put the account into OVERDRAWN by withdrawing $50 (balance 0, limit 100)
        self.account_empty.withdraw(50)
        self.assertEqual(self.account_empty.status, "OVERDRAWN")

        # Deposit exactly $50 to bring balance back to 0
        result = self.account_empty.deposit(50)

        # deposit() should return True on success
        self.assertTrue(result)

        # Balance should be back to 0.0
        self.assertEqual(self.account_empty.balance, 0.0)

        # Status should transition from OVERDRAWN back to ACTIVE
        self.assertEqual(self.account_empty.status, "ACTIVE")

        # Two transaction records: one withdrawal and one deposit
        self.assertEqual(len(self.account_empty.transaction_history), 2)

        # get_summary() should reflect ACTIVE status and updated count
        summary = self.account_empty.get_summary()
        self.assertEqual(summary["balance"], 0.0)
        self.assertEqual(summary["status"], "ACTIVE")
        self.assertEqual(summary["transaction_count"], 2)

    def test_transfer_between_accounts_multi_attributes(self):
        """
        Test fund transfer between two accounts.
        """
        # Transfer $50 from account_funded to account_empty with a $5 transfer fee
        result = self.account_funded.transfer_to(self.account_empty, 50, transfer_fee=5)

        # transfer_to() should return True on success
        self.assertTrue(result)

        # Sender balance: 200 - 50 - 5 = 145
        self.assertEqual(self.account_funded.balance, 145.0)

        # Sender status should remain ACTIVE
        self.assertEqual(self.account_funded.status, "ACTIVE")

        # Sender should have 2 records: initial deposit + withdrawal
        self.assertEqual(len(self.account_funded.transaction_history), 2)

        # Verify the sender's withdrawal record (transfer_to calls withdraw internally)
        sender_tx = self.account_funded.transaction_history[1]
        self.assertEqual(sender_tx["type"], "WITHDRAWAL")
        self.assertEqual(sender_tx["amount"], 50.0)
        self.assertEqual(sender_tx["fee"], 5.0)
        self.assertEqual(sender_tx["balance_after"], 145.0)

        # Recipient balance: 0 + 50 = 50
        self.assertEqual(self.account_empty.balance, 50.0)

        # Recipient status should remain ACTIVE
        self.assertEqual(self.account_empty.status, "ACTIVE")

        # Recipient should have 1 record: deposit from transfer
        self.assertEqual(len(self.account_empty.transaction_history), 1)

        # Verify the recipient's deposit record
        recipient_tx = self.account_empty.transaction_history[0]
        self.assertEqual(recipient_tx["type"], "DEPOSIT")
        self.assertEqual(recipient_tx["amount"], 50.0)
        self.assertEqual(recipient_tx["fee"], 0.0)
        self.assertEqual(recipient_tx["balance_after"], 50.0)

        # Verify both summaries
        sender_summary = self.account_funded.get_summary()
        self.assertEqual(sender_summary["balance"], 145.0)
        self.assertEqual(sender_summary["transaction_count"], 2)

        recipient_summary = self.account_empty.get_summary()
        self.assertEqual(recipient_summary["balance"], 50.0)
        self.assertEqual(recipient_summary["transaction_count"], 1)

    def test_frozen_account_restrictions(self):
        """
        Test that a FROZEN account rejects deposits, withdrawals, and transfers with RuntimeError.
        """
        # Freeze the funded account
        self.account_funded.freeze()

        # Status should now be FROZEN
        self.assertEqual(self.account_funded.status, "FROZEN")

        # Deposit into a frozen account should raise RuntimeError
        with self.assertRaises(RuntimeError):
            self.account_funded.deposit(100)

        # Withdraw from a frozen account should raise RuntimeError
        with self.assertRaises(RuntimeError):
            self.account_funded.withdraw(50)

        # Transfer from a frozen account should raise RuntimeError
        with self.assertRaises(RuntimeError):
            self.account_funded.transfer_to(self.account_empty, 50)

        # Transfer to a frozen account should also raise RuntimeError
        with self.assertRaises(RuntimeError):
            self.account_empty.transfer_to(self.account_funded, 10)

        # Unfreeze and verify status restores correctly (balance 200 > 0, so ACTIVE)
        self.account_funded.unfreeze()
        self.assertEqual(self.account_funded.status, "ACTIVE")

        # After unfreezing, deposit should work again
        self.account_funded.deposit(50)
        self.assertEqual(self.account_funded.balance, 250.0)

    def test_invalid_operations_raise_exceptions(self):
        """
        Test exception handling
        """
        # deposit() rejects non-positive amounts
        with self.assertRaises(ValueError):
            self.account_empty.deposit(0)
        with self.assertRaises(ValueError):
            self.account_empty.deposit(-10)

        # withdraw() rejects non-positive amounts
        with self.assertRaises(ValueError):
            self.account_funded.withdraw(0)
        with self.assertRaises(ValueError):
            self.account_funded.withdraw(-10)

        # withdraw() rejects a negative fee
        with self.assertRaises(ValueError):
            self.account_funded.withdraw(10, fee=-1)

        # withdraw() rejects amounts that exceed balance + overdraft limit
        # account_empty has balance 0 and overdraft limit 100; total deductible = 100
        with self.assertRaises(ValueError):
            self.account_empty.withdraw(101)

        # transfer_to() rejects a non-BankAccount target
        with self.assertRaises(TypeError):
            self.account_funded.transfer_to("not_an_account", 50)

        # transfer_to() rejects non-positive transfer amounts
        with self.assertRaises(ValueError):
            self.account_funded.transfer_to(self.account_empty, 0)
        with self.assertRaises(ValueError):
            self.account_funded.transfer_to(self.account_empty, -50)

        # BankAccount constructor rejects negative initial balance
        with self.assertRaises(ValueError):
            BankAccount("ACC003", "Charlie", initial_balance=-100)

        # BankAccount constructor rejects negative overdraft limit
        with self.assertRaises(ValueError):
            BankAccount("ACC004", "Diana", overdraft_limit=-50)


if __name__ == "__main__":
    unittest.main()
