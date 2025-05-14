
import unittest
from unittest.mock import MagicMock
from datetime import datetime
from app import logic
from app.logic import process_leave_application, convert_cl_to_al

class TestLeaveApplication(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.user = MagicMock()
        self.user.id = 1
        self.user.username = "rahulboy"
        self.user.team_id = 101
        self.user.team.manager_id = 99
        self.db.get.return_value = self.user

        # Patch logic helpers
        logic.get_monthly_leave_count = MagicMock(return_value=0)
        logic.get_team_shrinkage = MagicMock(return_value=5.0)
        logic.get_leave_balance = MagicMock(return_value=10)
        logic.decrement_leave_balance = MagicMock(return_value=True)
        logic.send_leave_email = MagicMock()
        logic.send_manager_email = MagicMock()

    def test_convert_cl_to_al(self):
        start = datetime(2025, 5, 1).date()
        end = datetime(2025, 5, 3).date()
        result = convert_cl_to_al("CL", start, end)
        self.assertEqual(result, "AL")

    def test_short_cl_remains_cl(self):
        start = datetime(2025, 5, 1).date()
        end = datetime(2025, 5, 2).date()
        result = convert_cl_to_al("CL", start, end)
        self.assertEqual(result, "CL")

    def test_optional_leave_rejected(self):
        data = {
            'user_id': 1,
            'leave_type': 'Optional',
            'start_date': '2025-05-01',
            'end_date': '2025-05-04',
            'is_half_day': False
        }
        result = process_leave_application(self.db, data)
        self.assertEqual(result['message'], "Leave rejected successfully")

    def test_sick_leave_pending(self):
        data = {
            'user_id': 1,
            'leave_type': 'Sick',
            'start_date': '2025-05-01',
            'end_date': '2025-05-01',
            'is_half_day': False
        }
        result = process_leave_application(self.db, data)
        self.assertEqual(result['message'], "Leave pending successfully")

    def test_approved_leave(self):
        data = {
            'user_id': 1,
            'leave_type': 'AL',
            'start_date': '2025-05-01',
            'end_date': '2025-05-01',
            'is_half_day': False
        }
        result = process_leave_application(self.db, data)
        self.assertEqual(result['message'], "Leave approved successfully")

    def test_fcfs_threshold_exceeded(self):
        logic.get_team_shrinkage = MagicMock(return_value=12.0)
        data = {
            'user_id': 1,
            'leave_type': 'AL',
            'start_date': '2025-05-01',
            'end_date': '2025-05-01',
            'is_half_day': False
        }
        result = process_leave_application(self.db, data)
        self.assertEqual(result['message'], "Leave pending successfully")

    def test_insufficient_balance(self):
        logic.get_leave_balance = MagicMock(return_value=0)
        data = {
            'user_id': 1,
            'leave_type': 'AL',
            'start_date': '2025-05-01',
            'end_date': '2025-05-01',
            'is_half_day': False
        }
        result = process_leave_application(self.db, data)
        self.assertEqual(result['message'], "Leave pending successfully")

    def test_monthly_threshold_exceeded(self):
        logic.get_monthly_leave_count = MagicMock(return_value=6)
        data = {
            'user_id': 1,
            'leave_type': 'AL',
            'start_date': '2025-05-01',
            'end_date': '2025-05-01',
            'is_half_day': False
        }
        result = process_leave_application(self.db, data)
        self.assertEqual(result['message'], "Leave pending successfully")

if __name__ == '__main__':
    unittest.main()
