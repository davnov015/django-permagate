from __future__ import annotations
from django.conf import settings
import importlib
from typing import Optional


class Permission:
    _root: Optional[Permission] = None

    @classmethod
    def get_root(cls, root_path: Optional[str] = None):
        """
        Loads the root permission from the PERMAGATE_PERMISSIONS environmental variable or the specified root path.
        The PERMAGATE_PERMISSIONS variable contains the path to the module that contains the root permission object. An
        optional suffix of the form ":variable_name" may be appended to the path to specify the name of the variable
        referencing the root permission, however if it's not specified, it's assumed the permission object is referenced
        by a variable named "root". Once loaded, the root permission will be cached, unless a custom root path is
        specified.
        :param root_path: A path to the root permission that overrides the value in PERMAGATE_PERMISSIONS
        :return: The root permission object
        """
        if not cls._root or root_path:
            cls._root = cls._load_permission_root(root_path)
        return cls._root

    @staticmethod
    def _load_permission_root(root_path: Optional[str] = None) -> Permission:
        """
        Loads the root permission from the PERMAGATE_PERMISSIONS environmental variable. The PERMAGATE_PERMISSIONS
        variable contains the path to the module that contains the root permission object. An optional suffix of the
        form ":variable_name" may be appended to the path to specify the name of the variable referencing the root
        permission, however if it's not specified, it's assumed the permission object is referenced by a variable named
        "root".
        :param root_path: A path to the root permission that overrides the value in PERMAGATE_PERMISSIONS
        :return: The root permission object
        """
        root_path = root_path or settings.PERMAGATE_PERMISSIONS
        root_variable_name = "root"
        assert isinstance(root_path, str), "PERMAGATE_PERMISSIONS was not initialized!"
        if ":" in root_path:
            components = root_path.split(":")
            assert (
                len(components) == 2
            ), "Invalid PERMAGATE_PERMISSIONS string, it may contain at most one ':'"
            root_path = components[0]
            root_variable_name = components[1]
        module = importlib.import_module(root_path)
        root_permission = getattr(module, root_variable_name)
        assert (
            isinstance(root_permission, Permission) and root_permission.is_root
        ), "PERMAGATE_PERMISSIONS did not point to a root Permissions object"
        return root_permission

    def __init__(
        self,
        key: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Defines a permission. The root permission whose role is to contain all other permissions is signified by a blank
        key.
        :param key: The permission key - should not contain key separator ('.'), inclusive wildcard ('>'), or root
        permission key ('*')
        :param name: The name of the permission, visible in the control interface
        :param description: The permission description, visible in the control interface
        """
        assert (
            not key or "." not in key
        ), "A permission key must be equivalent to one permission string segment"
        assert (
            not key or ">" not in key
        ), "Permission keys cannot contain inclusive wildcards, use those in permission strings assigned to users/groups"
        assert (
            not key or "*" not in key
        ), "The '*' character is reserved. Leave the key blank to create a root permission instance"
        self._key = key
        self.name = name
        self.description = description
        self._parent: Optional[Permission] = None
        self._children: list[Permission] = []

    @property
    def key(self):
        return self._key or "*"

    @property
    def is_root(self):
        """
        A permission instance is the root permission if the key is blank.
        :return: True if this is the root permission
        """
        return not self._key

    @property
    def absolute_permission(self) -> str:
        """
        Determines the full permission string by taking the parent permission into consideration.
        :return: The absolute permission string
        """
        if self._parent and not self._parent.is_root:
            return f"{self._parent.absolute_permission}.{self.key}"
        return self.key

    def register(self, permissions: list[Permission]):
        """
        Registers a list of permissions as child permissions.
        :param permissions: A permission list
        :return:
        """
        for permission in permissions:
            assert permission.key, "The root permission cannot be registered as a child"
            permission._parent = self
        self._children += permissions
        return self

    def exists(self, permission: str):
        """
        Checks if an absolute permission exists.
        :param permission: The permission string, may end with an inclusive wildcard character ('>') or the root
        reference character ('*')
        :return: True if the permission string is defined in this permission tree
        """
        # If it ends with a wildcard, remove the wildcard
        if permission.endswith(">"):
            permission = permission[:-1]

        assert not permission.startswith(
            ">"
        ), "Permission strings cannot start with an inclusive wildcard"

        if permission.startswith("*"):
            assert (
                permission == "*"
            ), "The root permission string may only contain the root permission reference ('*')"

        keys = permission.split(".")
        if len(keys):
            assert len(keys[0]), "Permission string segments cannot be blank"
            key_matches = keys[0] == self.key
            if key_matches or self.is_root:
                if key_matches:
                    keys = keys[1:]

                if len(keys):
                    permission = ".".join(keys)
                    for child in self._children:
                        if child.exists(permission):
                            return True
                elif key_matches:
                    return True  # We're at the last permission segment and the current key matched
        return False

    @property
    def permission_list(self) -> list[str]:
        """
        Retrieves a list of all available permission strings that may be assigned to users. The list includes the
        permission represented by the current instance as well as the child permissions.
        :return:
        """
        permissions = [self.absolute_permission]
        if len(self._children) and not self.is_root:
            permissions.append(f"{self.absolute_permission}>")

        for child in self._children:
            permissions += child.permission_list
        return permissions
