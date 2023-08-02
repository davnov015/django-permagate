from __future__ import annotations
from typing import Optional


class Permission:
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
