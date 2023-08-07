from .permission import Permission


root = Permission().register(
    [
        Permission("test", "Test", "Test permission").register(
            [
                Permission("sub1", "Sub perm"),
                Permission("sub2"),
                Permission("sub3").register(
                    [
                        Permission("sub"),
                    ]
                ),
            ]
        ),
        Permission("test2", "Test", "Test perm"),
    ]
)

rootTwo = Permission().register(
    [
        Permission("test", "2nd root", "Test permission").register(
            [
                Permission("sub1", "Sub perm"),
                Permission("sub2"),
            ]
        ),
        Permission("test2", "Test", "Test perm"),
    ]
)
