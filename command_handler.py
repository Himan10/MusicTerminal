# Implementing a command handler
# Inspired by : How does discord implements a functionality to run commands based on the user
# input without having large IF/ELIF statements?  

# Store the function/method Object into a dictionary
# store format : {callback.__name__: Commands.__repr__}
# Call it from there
# Run it

from typing import Callable

# Exceptions
class CommandRegistrationError(Exception):
    pass

class CommandNotCallable(Exception):
    
    def __init__(self, *args):
        # tuple default size = 24
        self.message = lambda x: x[0] if x.__sizeof__() > 24 else None
        self.message = self.message(args)

    def __str__(self):
        if self.message:
            return f"{self.message}"
        return "type Object is not callable"


# Class that converts function into a command
class Command:

    def __init__(self, func: Callable) -> None:
        self.func = lambda x: callable(func)
        if not self.func(func):
            raise CommandNotCallable(f"{type(func)!r} not callable")
        self.func = func

    def __repr__(self) -> str:
        return repr(f'<Command: {self.func.__name__.lower()!r}>')

# Class that registers the command (store in dictionary)
class Commands:

    commands_dict = {} # class attribute

    @classmethod
    def add_command(cls, command: Command) -> None:
        if command in cls.commands_dict:
            raise CommandRegistrationError("Already Registered")
        if not isinstance(command, Command):
            raise TypeError(f"{command} is not a subclass of Command")
        cls.commands_dict[command.func.__name__] = command.func

# Class acts as a bot, and will run functions
# Parent of this class will be `Commands`
class InputParser(Commands):

    def __init__(self, command_prefix: str):
        super().__init__()
        self.command_prefix = command_prefix # length = 1
    
    @classmethod
    def command(cls, callback: Callable) -> None:
        """ used as a decorator to register function
        as type :class: `Command` and returns the
        associated function object with it.

        staticmethod doesn't need `self` coz it
        wont depend on instance to access it, simply
        Class.command(callback)
        """
        try:
            Commands.add_command(Command(callback))
            return Commands.commands_dict.get(callback.__name__, None)
        except Exception as err:
            return print(err.args[0])

    def process_command(self, user_input: str) -> None:
        if not user_input.startswith(self.command_prefix):
            return

        command_name, *args = user_input[1:].split(' ')
        command_method = self.commands_dict.get(command_name, None)

        if not command_method:
            return print('Not a valid command, Not registered')
        
        try:
            return command_method(self, *args) # run the command and return the result
        except Exception as err:
            print(f" --- use arguments with {command_method.__name__} --- ")
