from django.db.models import QuerySet
from django.conf import settings
from .models import UserPermission, GroupPermission, User
from .permission import Permission
from typing import Optional
import importlib
import logging


logger = logging.getLogger(__name__)


def has_permission(
    user: User, permission: str, _test_permissions_path: Optional[str] = None
) -> bool:
    """
    Verifies that a user has a specific permission, or is a member of a group that has the permission. Note that the
    permission string "a.b>" implies that a user has the a.b permission as well as all child permissions.
    :param user:
    :param permission:
    :param _test_permissions_path: Overrides the PERMAGATE_PERMISSIONS value (for testing only)
    :return: True if the user has the specified permission
    """
    root: Permission = _load_permission_root(_test_permissions_path)
    if root.exists(permission):
        user_permission = _has_permission(user.permagate_permissions.all(), permission)
        if not user_permission:
            for group in user.groups.all():
                group_permissions = group.permagate_permissions.all()
                if _has_permission(group_permissions, permission):
                    return True
        else:
            return user_permission
    else:
        logger.warning(f"Checking for permission {permission} that does not exist")
    return False


def _load_permission_root(permissions_path: Optional[str] = None) -> Permission:
    """
    Loads the root permission from the PERMAGATE_PERMISSIONS environmental variable. The PERMAGATE_PERMISSIONS variable
    contains the path to the module that contains the root permission object. An optional suffix of the form
    ":variable_name" may be appended to the path to specify the name of the variable referencing the root permission,
    however if it's not specified, it's assumed the permission object is referenced by a variable named "root".
    :param permissions_path: A path to the root permission that overrides the value in PERMAGATE_PERMISSIONS
    :return: The root permission object
    """
    permissions_path = permissions_path or settings.PERMAGATE_PERMISSIONS
    root_variable_name = "root"
    assert isinstance(
        permissions_path, str
    ), "PERMAGATE_PERMISSIONS was not initialized!"
    if ":" in permissions_path:
        components = permissions_path.split(":")
        assert (
            len(components) == 2
        ), "Invalid PERMAGATE_PERMISSIONS string, it may contain at most one ':'"
        permissions_path = components[0]
        root_variable_name = components[1]
    module = importlib.import_module(permissions_path)
    root_permission = getattr(module, root_variable_name)
    assert (
        isinstance(root_permission, Permission) and root_permission.is_root
    ), "PERMAGATE_PERMISSIONS did not point to a root Permissions object"
    return root_permission


def _has_permission(
    queryset: QuerySet[UserPermission, GroupPermission],
    permission: str,
    wildcard_only: bool = False,
) -> bool:
    """
    Determines if a given permission is contained in the specified queryset while considering the inclusive wildcard
    operator '>'. The root permission ('*') is also considered.
    :param queryset: The queryset we're operating on
    :param permission: The permission we're looking up
    :param wildcard_only: Only check if the permission string w/ an appended wildcard character is found in the queryset
    :return: True if the queryset contains the permission
    """
    assert (
        ">" not in permission
    ), "A required permission cannot contain an inclusive wildcard '>'"
    assert len(permission) > 0, "The permission string cannot be empty"
    found = (
        not wildcard_only
        and (
            queryset.filter(permission=permission).exists()
            or queryset.filter(permission="*")
        )
    ) or queryset.filter(permission=f"{permission}>").exists()
    if found:
        return True
    path_segments = permission.split(".")
    path_segments.pop()
    # If there are no segments left in the permission string, the permission was not found
    if not path_segments:
        return False
    permission = ".".join(path_segments)
    # If not set, this is our first run, narrow down the queryset (performance gain?)
    if not wildcard_only:
        queryset = queryset.filter(permission__iendswith=">")
    return _has_permission(queryset, permission, True)
