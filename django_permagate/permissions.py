from permagate.permission import Permission

root = Permission().register(
    [
        Permission("test", "Test", "Test permission").register(
            [
                Permission("sub1", "Sub perm"),
                Permission("sub2"),
            ]
        ),
        Permission("test2", "Test", "Test perm"),
    ]
)
