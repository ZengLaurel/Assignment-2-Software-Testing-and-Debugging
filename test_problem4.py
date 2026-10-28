"""
Unit tests for Problem 4: MeetingRoom

Instructions:
Complete the unit test methods below using Python's unittest framework.
Your test methods must assert MULTIPLE ATTRIBUTES on the MeetingRoom object
(e.g., bookings list, total_hours_booked, free slots, utilization rate)
to verify room state and conflict management.

Running tests:
    python -m unittest test_problem4.py -v
"""
import unittest
from problem4 import MeetingRoom


class TestMeetingRoom(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.room = MeetingRoom("Conference-A", capacity=10)

    def test_initial_state(self):
        """Verify initial state of an empty meeting room."""
        self.assertEqual(self.room.room_id, "Conference-A")
        self.assertEqual(self.room.capacity, 10)
        self.assertEqual(self.room.bookings, [])
        self.assertEqual(self.room.total_hours_booked, 0)
        self.assertFalse(self.room.is_maintenance)
        self.assertEqual(self.room.get_free_slots(8, 18), [(8, 18)])
        self.assertEqual(self.room.get_utilization_rate(10), 0.0)

        # Invalid capacity raises ValueError
        with self.assertRaises(ValueError):
            MeetingRoom("Room-B", capacity=0)

    def test_single_booking(self):
        """Book B001 from 9 to 12 with 5 attendees; verify all attributes."""
        result = self.room.book("B001", "Sprint Planning", 9, 12, 5)

        self.assertTrue(result)
        self.assertEqual(len(self.room.bookings), 1)

        b = self.room.bookings[0]
        self.assertEqual(b["booking_id"], "B001")
        self.assertEqual(b["title"], "Sprint Planning")
        self.assertEqual(b["start_time"], 9)
        self.assertEqual(b["end_time"], 12)
        self.assertEqual(b["attendees"], 5)

        self.assertEqual(self.room.total_hours_booked, 3)
        self.assertEqual(self.room.get_utilization_rate(10), 0.3)

        # Free slots: 8-9 and 12-18
        self.assertEqual(self.room.get_free_slots(8, 18), [(8, 9), (12, 18)])

    def test_back_to_back_allowed(self):
        """Back-to-back bookings (9-11 then 11-13) must not conflict."""
        self.room.book("B002", "Daily Standup", 9, 11, 3)
        self.room.book("B003", "Design Review", 11, 13, 8)

        self.assertEqual(len(self.room.bookings), 2)
        self.assertEqual(self.room.total_hours_booked, 4)
        # Free slots: 8-9 and 13-18
        self.assertEqual(self.room.get_free_slots(8, 18), [(8, 9), (13, 18)])
        self.assertEqual(self.room.get_utilization_rate(10), 0.4)

    def test_overlapping_rejected(self):
        """Overlapping bookings must raise ValueError and leave state unchanged."""
        self.room.book("B004", "Meeting A", 9, 12, 4)

        # Overlaps at the start
        with self.assertRaises(ValueError):
            self.room.book("B005", "Meeting B", 10, 14, 3)

        # Completely inside existing booking
        with self.assertRaises(ValueError):
            self.room.book("B006", "Meeting C", 10, 11, 2)

        # State must be unchanged after failed attempts
        self.assertEqual(len(self.room.bookings), 1)
        self.assertEqual(self.room.total_hours_booked, 3)

    def test_cancel_booking(self):
        """Cancel one of two bookings; verify bookings list and total_hours_booked."""
        self.room.book("B007", "Team Sync", 8, 10, 5)
        self.room.book("B008", "Tech Talk", 13, 16, 6)

        result = self.room.cancel("B007")

        self.assertTrue(result)
        self.assertEqual(len(self.room.bookings), 1)
        self.assertEqual(self.room.bookings[0]["booking_id"], "B008")
        self.assertEqual(self.room.total_hours_booked, 3)   # only B008 (3h) remains
        # B007 slot restored: 8-13 now free
        self.assertEqual(self.room.get_free_slots(8, 18), [(8, 13), (16, 18)])

        # Cancelling non-existent ID raises KeyError
        with self.assertRaises(KeyError):
            self.room.cancel("B999")

    def test_exceptions(self):
        """Attendees over capacity, bad times, duplicate ID, maintenance, bad cancel."""
        # Attendees exceed capacity (10)
        with self.assertRaises(ValueError):
            self.room.book("B010", "Big Meeting", 9, 11, 11)

        # end_time <= start_time
        with self.assertRaises(ValueError):
            self.room.book("B010", "Bad Time", 10, 10, 3)
        with self.assertRaises(ValueError):
            self.room.book("B010", "Bad Time", 12, 9, 3)

        # Negative start time
        with self.assertRaises(ValueError):
            self.room.book("B010", "Negative", -1, 9, 3)

        # Duplicate booking ID
        self.room.book("B010", "First", 9, 10, 2)
        with self.assertRaises(ValueError):
            self.room.book("B010", "Duplicate", 14, 16, 2)

        # Maintenance blocks booking
        self.room.is_maintenance = True
        with self.assertRaises(RuntimeError):
            self.room.book("B011", "Blocked", 11, 12, 2)


if __name__ == "__main__":
    unittest.main()
