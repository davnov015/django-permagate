from django.test import TestCase
from django.contrib.auth.models import User as UserType, Group
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .permission import Permission
from .core import has_permission
from .models import UserPermission, GroupPermission, validate_permission
from typing import Type

User: Type[UserType] = get_user_model()

# Create your tests here.


class PermissionLoaderTest(TestCase):
    def test_default_loading(self, path_override=None):
        path_override = path_override or "permagate.test_permissions"
        root = Permission.get_root(path_override)
        self.assertEqual(isinstance(root, Permission), True)
        self.assertEqual(root.is_root, True)

    def test_specific_loading(self):
        self.test_default_loading("permagate.test_permissions:rootTwo")


class PermissionTest(TestCase):
    def setUp(self) -> None:
        self.root = Permission.get_root("permagate.test_permissions")

    def test_root(self):
        self.assertTrue(self.root.exists("test"))
        self.assertTrue(self.root.exists("test.sub1"))
        self.assertTrue(self.root.exists("test.sub2"))
        self.assertFalse(self.root.exists("test.sub4"))
        self.assertTrue(self.root.exists("test2"))
        self.assertTrue(self.root.exists("*"))
        self.assertTrue(self.root.exists("test>"))
        self.assertRaises(AssertionError, self.root.exists, "*.test")
        self.assertRaises(AssertionError, self.root.exists, ">")

    def test_permission_list(self):
        expected_list = [
            "*",
            "test",
            "test>",
            "test.sub1",
            "test.sub2",
            "test.sub3",
            "test.sub3>",
            "test.sub3.sub",
            "test2",
        ]
        self.assertEqual(self.root.permission_list, expected_list)

    def test_model_validator(self):
        self.assertRaises(ValidationError, validate_permission, "t*st")
        self.assertRaises(ValidationError, validate_permission, "test.sub0")
        self.assertIsNone(validate_permission("*"))
        self.assertIsNone(validate_permission("test>"))


class HasPermissionTest(TestCase):
    path = "permagate.test_permissions"

    def setUp(self) -> None:
        Permission.get_root(self.path)
        self.group, _ = Group.objects.get_or_create(name="test")
        self.user, _ = User.objects.get_or_create(username="tester")
        self.userTwo, _ = User.objects.get_or_create(username="tester2")
        self.rootUser, _ = User.objects.get_or_create(username="root_tester")
        self.group.user_set.add(self.user)
        UserPermission.objects.get_or_create(user=self.user, permission="test.sub1")
        GroupPermission.objects.get_or_create(group=self.group, permission="test.sub3")
        UserPermission.objects.get_or_create(user=self.userTwo, permission="test>")
        UserPermission.objects.get_or_create(user=self.rootUser, permission="*")

    def test_user_permissions(self):

        # Perform negative test
        self.assertFalse(has_permission(self.user, "test"))
        self.assertFalse(has_permission(self.user, "test2"))
        self.assertFalse(has_permission(self.user, "test.sub2"))

        # Test direct assignment
        self.assertTrue(has_permission(self.user, "test.sub1"))

        # Test assignment via group
        self.assertTrue(has_permission(self.user, "test.sub3"))

    def test_inclusive_wildcard(self):
        # Accessible via wildcard
        self.assertTrue(has_permission(self.userTwo, "test"))
        self.assertTrue(has_permission(self.userTwo, "test.sub1"))
        self.assertTrue(has_permission(self.userTwo, "test.sub2"))
        self.assertTrue(has_permission(self.userTwo, "test.sub3.sub"))

        # Negative test
        self.assertFalse(has_permission(self.userTwo, "test2"))

    def test_validation(self):
        self.assertRaises(AssertionError, has_permission, self.userTwo, "test>")

    def test_root_permission(self):
        self.assertTrue(has_permission(self.rootUser, "test.sub1"))
        self.assertTrue(has_permission(self.rootUser, "test"))
        self.assertTrue(has_permission(self.rootUser, "test2"))
