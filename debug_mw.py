import main
print(main.__file__)
print([m.cls.__name__ for m in main.app.user_middleware])
