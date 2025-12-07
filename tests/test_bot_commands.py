import asyncio

from app.bot import setup_bot_commands


class FakeBot:
    def __init__(self) -> None:
        self.commands = None

    async def set_my_commands(self, commands):
        self.commands = commands


def test_setup_bot_commands_sets_all_commands() -> None:
    bot = FakeBot()
    asyncio.run(setup_bot_commands(bot))
    assert bot.commands is not None
    names = [cmd.command for cmd in bot.commands]
    assert names == ["start", "help", "settings"]
