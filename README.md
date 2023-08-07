# PermaGate

PermaGate is a Django permissions system which offers hierarchical permissions that can be
directly to users and groups.

# Installation

1. ```pip install django-permagate``` to install the package
2. ```python 
   # Add it to the list of installed apps in Django's settings.py:
   INSTALLED_APPS = [
        ...,
        "permagate",
   ]
   ```
3. ```python manage.py migrate``` to create the permission models
4. Set the ```PERMAGATE_PERMISSIONS``` settings variable to the module defining the root permission (see below)

# Usage

## Defining Permissions

The list of permissions that may be assigned to users and groups is defined using the 
Permission class. A root permission object is used as the starting point of the permission
tree and is created by calling
```Permission()``` with the default constructor parameters. Child permission nodes can be
added to the permission tree by calling the
```register()``` function on a permission and passing the list of child permissions:

```python
from permagate.permission import Permission
root = Permission().register([
    Permission("test", "Optional Name", "Optional Description").register([
        Permission("sub1").register([
            Permission("sub-sub1")
        ]),
        Permission("sub2"),
    ]),
    Permission("test1"),
])

# In this case, root.permission_list will return:
# ['*', 
# 'test', 
# 'test>', 
# 'test.sub1', 
# 'test.sub1>', 
# 'test.sub1.sub-sub1', 
# 'test.sub2', 
# 'test1']
#
# This is the list of permission strings that may be assigned to users and groups.

```

The settings variable ```PERMAGATE_PERMISSIONS``` should be set to the path of the 
module defining the root permission variable:
```python
# Assuming there's a permissions.py file in mymodule containing a variable named 'root' 
# that contains the root permission:
PERMAGATE_PERMISSIONS = "mymodule.permissions"
```

It is possible to store the permission root in a variable named something other than
```root``` by suffixing the path with ```:new_root_name```:
```python
PERMAGATE_PERMISSIONS = "mymodule.permissions:permission_root"
```

## Using Permissions

Permissions in the user-defined hierarchy may be referenced using dot-separated strings,
where each string segment is a permission key. The '*' and '>' are special characters
where:
1. '>' is referred as the inclusive wildcard since it references the current permission and its children
2. '*' references the root permission and is considered as its key

To assign user and group permissions and check user access:

```python
from permagate.models import UserPermission, GroupPermission
from permagate.core import has_permission
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# Assign a permission to a user
test_user = User.objects.create(username="test")
UserPermission.objects.create(user=test_user, permission="test>")

# Assign a permission to a group
test_group = Group.objects.create(group="test")
GroupPermission.objects.create(group=test_group, permission="test.sub1>")

test_user_two = User.objects.create(username="test2")
test_group.user_set.add(test_user_two)

if has_permission(test_user, "test.sub1"):
    print(f"User {test_user.username} has permission test.sub1 due to directly assignment")

if has_permission(test_user_two, "test.sub1"):
    print(f"fUser {test_user_two.username} has permission test.sub1 via group assignment")
```

Note that the permission strings assigned to users may include the inclusive wildcard
character while absolute permissions strings must be used when checking user permissions.
