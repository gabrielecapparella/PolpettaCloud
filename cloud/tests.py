#from django.test import TestCase
import unittest
from unittest.mock import patch, call

from cloud.models import GDrive_Index, CloudUser
import cloud.google_api as g_api

# will test on production db, BAD GAB!
class GoogleApiTest(unittest.TestCase):
	def setUp(self):
		self.user = CloudUser.objects.get(username="test")
		GDrive_Index.objects.filter(user=self.user).delete()

	def tearDown(self):
		#GDrive_Index.objects.filter(user=self.user).delete()
		pass

	@unittest.skip
	def test_upload_and_delete_file(self): # I know, not an unit test
		test_file = GDrive_Index.objects.create(
			user = self.user,
			gdrive_id = "",
			parent_gdrive_id = "",
			path = "test.txt",
			is_dirty = False,
			is_dir = False
		)
		upload = g_api.gdrive_upload_file(self.user, test_file)
		self.assertEqual(upload["id"], test_file.gdrive_id)

		delete = g_api.gdrive_delete(self.user, test_file)
		self.assertEqual(delete.status_code, 204)
		self.assertEqual(test_file.id, None)

	@unittest.skip
	def test_check_dirty_was_deleted(self):
		with patch.object(g_api, 'gdrive_delete') as mock:
			GDrive_Index.objects.create(
				user = self.user,
				gdrive_id = "anatra",
				parent_gdrive_id = "",
				path = "file_that_doesnt_exist.txt",
				is_dirty = True,
				is_dir = False
			)
			g_api.gdrive_check_dirty(self.user)
			mock.assert_called()

	@unittest.skip
	def test_check_dirty_new_single_file(self):
		with patch.object(g_api, 'gdrive_upload_file') as mock:
			GDrive_Index.objects.create(
				user = self.user,
				gdrive_id = "",
				parent_gdrive_id = "actual_parent_id",
				path = "test.txt",
				is_dirty = True,
				is_dir = False
			)
			g_api.gdrive_check_dirty(self.user)
			mock.assert_called()

	def test_check_dirty_new_file_with_new_parent(self):
		with patch.object(g_api, 'gdrive_upload_file') as mock:
			test_file = GDrive_Index.objects.create(
				user = self.user,
				gdrive_id = "",
				parent_gdrive_id = "",
				path = "test/test.txt",
				is_dirty = True,
				is_dir = False
			)
			test_parent = GDrive_Index.objects.create(
				user = self.user,
				gdrive_id = "",
				parent_gdrive_id = "",
				path = "test",
				is_dirty = True,
				is_dir = True
			)

			def set_gdrive_id(u, e): e.gdrive_id = "anatra"

			mock.side_effect = set_gdrive_id
			g_api.gdrive_check_dirty(self.user)
			calls = [call(self.user, test_parent), call(self.user, test_file)]
			
			self.assertEqual(mock.mock_calls, calls)

