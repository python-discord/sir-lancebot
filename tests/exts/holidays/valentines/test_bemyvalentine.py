
import pytest
import discord
# Import AsyncMock and MagicMock for creating fake asynchronous and regular objects for testing
from unittest.mock import AsyncMock, MagicMock
from discord.ext import commands
from bot.constants import Roles

# Import the BeMyValentine cog (the part of the bot that handles sending valentines) to be tested
from bot.exts.holidays.valentines.be_my_valentine import BeMyValentine



@pytest.mark.asyncio
async def test_send_valentine_user_without_lovefest_role():
    """Test that sending a valentine to a user without the lovefest role raises UserInputError."""
    # Create a fake bot instance using MagicMock
    bot = MagicMock()
    # Instantiate the BeMyValentine cog with the fake bot
    cog = BeMyValentine(bot)

    # Create a fake command context (ctx) using MagicMock
    ctx = MagicMock()
    # Set the delete method on the message to an AsyncMock since deletion is asynchronous
    ctx.message.delete = AsyncMock()
    # Create a fake command invoker (author) for the context
    ctx.author = MagicMock()
    # Create a fake user object representing the intended recipient
    user = MagicMock()
    # Simulate that the user does not have any roles by assigning an empty list
    user.roles = []  # User does not have the lovefest role

    # Assert that a UserInputError is raised when the command is called with a user missing the lovefest role
    with pytest.raises(commands.UserInputError, match="You cannot send a valentine to .* as they do not have the lovefest role!"):
        # Call the command callback with parameters for a public, signed valentine and expect an error due to missing role
        await cog.send_valentine.callback(cog, ctx, user, privacy_type="public", anon="signed", valentine_type="p")

    # Verify that the command did not attempt to delete the message since the process failed early
    ctx.message.delete.assert_not_called()  # No message should be deleted in this case



@pytest.mark.asyncio
async def test_send_valentine_self_valentine():
    """Test that a user cannot send a valentine to themselves."""
    # Create a fake bot instance
    bot = MagicMock()
    # Instantiate the BeMyValentine cog with the fake bot
    cog = BeMyValentine(bot)

    # Create a fake command context
    ctx = MagicMock()
    # Create a fake author for the command context
    ctx.author = MagicMock()
    # Set the delete method on the message to an AsyncMock
    ctx.message.delete = AsyncMock()
    # Use the same object for the user to simulate a self-send scenario
    user = ctx.author  # Self-send

    # Simulate that the user has the lovefest role by adding a role with the correct ID
    user.roles = [MagicMock(id=Roles.lovefest)]

    # Assert that sending a valentine to oneself raises a UserInputError with the expected message
    with pytest.raises(commands.UserInputError, match="Come on, you can't send a valentine to yourself"):
        # Call the command callback; self-send should trigger the error before any message is sent
        await cog.send_valentine.callback(cog, ctx, user, privacy_type="public", anon="signed", valentine_type="p")

    # Ensure that no attempt is made to delete the command message since the error occurs before deletion
    ctx.message.delete.assert_not_called()  # No need to delete the message in this case



@pytest.mark.asyncio
async def test_send_valentine_invalid_privacy_type():
    """Test that an invalid privacy type raises UserInputError."""
    # Create a fake bot instance
    bot = MagicMock()
    # Instantiate the BeMyValentine cog with the fake bot
    cog = BeMyValentine(bot)

    # Create a fake command context
    ctx = MagicMock()
    # Create a fake author for the command context
    ctx.author = MagicMock()
    # Create a fake recipient user
    user = MagicMock()
    # Simulate that the user has the lovefest role
    user.roles = [MagicMock(id=Roles.lovefest)]  # User has lovefest role

    # Assert that using an invalid privacy type (here, "invalid") raises a UserInputError with the correct message
    with pytest.raises(commands.UserInputError, match="Specify if you want the message to be sent privately or publicly!"):
        # Call the command callback with an invalid privacy type to trigger the error
        await cog.send_valentine.callback(cog, ctx, user, privacy_type="invalid", anon="signed", valentine_type="p")



@pytest.mark.asyncio
async def test_send_valentine_invalid_anon_type():
    """Test that an invalid anonymity type raises UserInputError."""
    # Create a fake bot instance
    bot = MagicMock()
    # Instantiate the BeMyValentine cog with the fake bot
    cog = BeMyValentine(bot)

    # Create a fake command context
    ctx = MagicMock()
    # Create a fake author for the command context
    ctx.author = MagicMock()
    # Create a fake recipient user
    user = MagicMock()
    # Simulate that the user has the lovefest role
    user.roles = [MagicMock(id=Roles.lovefest)]  # User has lovefest role

    # Assert that an invalid anonymity type (here, "invalid") causes a UserInputError with the expected message
    with pytest.raises(commands.UserInputError, match="Specify if you want the message to be anonymous or not!"):
        # Call the command callback with an invalid anonymity type to trigger the error
        await cog.send_valentine.callback(cog, ctx, user, privacy_type="public", anon="invalid", valentine_type="p")


@pytest.mark.asyncio
async def test_send_valentine_public_signed():
    """Test that a public, signed valentine is sent successfully."""
    # Create a fake bot instance
    bot = MagicMock()
    # Instantiate the BeMyValentine cog with the fake bot
    cog = BeMyValentine(bot)

    # Create a fake command context
    ctx = MagicMock()
    # Create a fake author for the command context
    ctx.author = MagicMock()
    # Set the delete method on the command message as an AsyncMock (should not be used in this case)
    ctx.message.delete = AsyncMock()
    # Set the send method on the context as an AsyncMock since the command sends a message publicly
    ctx.send = AsyncMock()
    # Create a fake recipient user object
    user = MagicMock()
    # Simulate that the recipient user has the lovefest role
    user.roles = [MagicMock(id=Roles.lovefest)]  # User has lovefest role
    # Define a display name for the recipient (used in the message embed)
    user.display_name = "Recipient"

    # Stub the random_emoji method to return fixed emojis for predictable output during testing
    cog.random_emoji = MagicMock(return_value=("💖", "💕"))
    # Stub the valentine_check method to return a sample valentine message and title
    cog.valentine_check = MagicMock(return_value=("A lovely poem", "A poem dedicated to"))

    # Call the send_valentine callback with valid parameters for a public, signed valentine
    await cog.send_valentine.callback(cog, ctx, user, privacy_type="public", anon="signed", valentine_type="p")

    # Assert that the context's send method was called to send the valentine publicly
    ctx.send.assert_awaited()  # Message should be sent publicly
    # Assert that the command message was not deleted since deletion is only required for anonymous messages
    ctx.message.delete.assert_not_called()  # No need to delete the message in this case



@pytest.mark.asyncio
async def test_send_valentine_private_anon():
    """Test that a private, anonymous valentine is sent successfully."""
    # Create a fake bot instance
    bot = MagicMock()
    # Instantiate the BeMyValentine cog with the fake bot
    cog = BeMyValentine(bot)

    # Create a fake command context
    ctx = MagicMock()
    # Create a fake author for the command context
    ctx.author = MagicMock()
    # Set the delete method on the command message as an AsyncMock for potential deletion
    ctx.message.delete = AsyncMock()
    # Set the send method on the author to simulate sending a DM confirmation back to the command invoker
    ctx.author.send = AsyncMock()
    # Create a fake recipient user object
    user = MagicMock()
    # Simulate that the recipient has the lovefest role
    user.roles = [MagicMock(id=Roles.lovefest)]  # User has lovefest role
    # Define a display name for the recipient used in messages
    user.display_name = "Recipient"
    # Set the recipient's send method as an AsyncMock to simulate sending the DM valentine
    user.send = AsyncMock()

    # Stub the random_emoji method to return fixed emojis for predictable testing output
    cog.random_emoji = MagicMock(return_value=("💖", "💕"))
    # Stub the valentine_check method to return a sample valentine message and title
    cog.valentine_check = MagicMock(return_value=("A lovely poem", "A poem dedicated to"))

    # Call the send_valentine callback with parameters for a private, anonymous valentine
    await cog.send_valentine.callback(cog, ctx, user, privacy_type="private", anon="anon", valentine_type="p")

    # Assert that the recipient's send method was awaited, indicating a DM was sent
    user.send.assert_awaited()  # DM should be sent
    # Assert that a confirmation DM was sent to the command invoker with the correct message
    ctx.author.send.assert_awaited_with(f"Your valentine has been **privately** delivered to {user.display_name}!")
    # Assert that the original command message was deleted to maintain anonymity
    ctx.message.delete.assert_awaited()  # Original command message should be deleted


@pytest.mark.asyncio
async def test_send_valentine_private_anon_dm_disabled():
    """Test that an error is raised when sending a private valentine to a user with DMs disabled."""
    # Create a fake bot instance
    bot = MagicMock()
    # Instantiate the BeMyValentine cog with the fake bot
    cog = BeMyValentine(bot)

    # Create a fake command context
    ctx = MagicMock()
    # Create a fake author for the command context
    ctx.author = MagicMock()
    # Set the delete method on the command message as an AsyncMock for potential deletion
    ctx.message.delete = AsyncMock()
    # Set the send method on the context as an AsyncMock to simulate sending error messages publicly
    ctx.send = AsyncMock()
    # Create a fake recipient user object
    user = MagicMock()
    # Simulate that the recipient has the lovefest role
    user.roles = [MagicMock(id=Roles.lovefest)]  # User has lovefest role
    # Define a display name for the recipient
    user.display_name = "Recipient"

    # Create a fake discord.Forbidden exception to simulate a scenario where the recipient's DMs are disabled
    forbidden_exception = discord.Forbidden(response=MagicMock(), message="Forbidden")
    # Set the recipient's send method to raise the Forbidden exception when called
    user.send = AsyncMock(side_effect=forbidden_exception)

    # Stub the random_emoji method to return fixed emojis for testing
    cog.random_emoji = MagicMock(return_value=("💖", "💕"))
    # Stub the valentine_check method to return a sample valentine message and title
    cog.valentine_check = MagicMock(return_value=("A lovely poem", "A poem dedicated to"))

    # Call the send_valentine callback with parameters for a private, anonymous valentine where the recipient's DMs are disabled
    await cog.send_valentine.callback(cog, ctx, user, privacy_type="private", anon="anon", valentine_type="p")

    # Assert that the context's send method was awaited with a message indicating that the DM could not be delivered
    ctx.send.assert_awaited_with(f"I couldn't send a private message to {user.display_name}. They may have DMs disabled.")
    # Assert that the original command message was deleted even in the error scenario
    ctx.message.delete.assert_awaited()  # Original command message should be deleted



@pytest.mark.asyncio
async def test_send_valentine_dm_channel():
    """Test that using the command in a DM (ctx.guild is None) raises UserInputError."""
    bot = MagicMock()
    cog = BeMyValentine(bot)

    ctx = MagicMock()
    ctx.guild = None  # Simulate a DM channel (no guild)
    ctx.message.delete = AsyncMock()
    ctx.author = MagicMock()

    user = MagicMock()
    user.roles = [MagicMock(id=Roles.lovefest)]
    user.display_name = "Recipient"

    with pytest.raises(commands.UserInputError, match="You are supposed to use this command in the server."):
        await cog.send_valentine.callback(cog, ctx, user, privacy_type="public", anon="signed", valentine_type="p")



@pytest.mark.asyncio
async def test_send_valentine_deletion_failure():
    """
    Test that if deleting the command message fails (raises discord.Forbidden),
    the bot sends an error message and continues processing.
    """
    bot = MagicMock()
    cog = BeMyValentine(bot)

    ctx = MagicMock()
    # Simulate deletion failure by having the delete method raise a Forbidden exception
    ctx.message.delete = AsyncMock(side_effect=discord.Forbidden(response=MagicMock(), message="Forbidden"))
    ctx.author = MagicMock()
    ctx.author.send = AsyncMock()
    ctx.send = AsyncMock()  # Used to send the error message for deletion failure
    ctx.guild = MagicMock()  # Ensure the command is executed in a guild

    user = MagicMock()
    user.roles = [MagicMock(id=Roles.lovefest)]
    user.display_name = "Recipient"
    user.send = AsyncMock()

    cog.random_emoji = MagicMock(return_value=("💖", "💕"))
    cog.valentine_check = MagicMock(return_value=("A lovely poem", "A poem dedicated to"))

    await cog.send_valentine.callback(cog, ctx, user, privacy_type="private", anon="anon", valentine_type="p")

    ctx.message.delete.assert_awaited()  # Confirm deletion was attempted
    # Confirm that an error message was sent due to deletion failure
    ctx.send.assert_any_await("I can't delete your message! Please check my permissions.")
    user.send.assert_awaited()  # Confirm that a DM was sent to the recipient
    ctx.author.send.assert_awaited_with(f"Your valentine has been **privately** delivered to {user.display_name}!")


@pytest.mark.asyncio
async def test_send_valentine_public_send_failure():
    """
    Test that if sending a public message fails (raises discord.Forbidden),
    the bot catches the exception and sends a fallback error message.
    """
    bot = MagicMock()
    cog = BeMyValentine(bot)

    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.message.delete = AsyncMock()  # Not used since anon is "signed"
    ctx.send = AsyncMock()
    # Simulate failure on the first call to ctx.send and then success on the fallback call
    ctx.send.side_effect = [discord.Forbidden(response=MagicMock(), message="Forbidden"), None]
    ctx.guild = MagicMock()

    user = MagicMock()
    user.roles = [MagicMock(id=Roles.lovefest)]
    user.display_name = "Recipient"

    cog.random_emoji = MagicMock(return_value=("💖", "💕"))
    cog.valentine_check = MagicMock(return_value=("A lovely poem", "A poem dedicated to"))

    await cog.send_valentine.callback(cog, ctx, user, privacy_type="public", anon="signed", valentine_type="p")

    # Confirm that the fallback error message was sent after the public message send failed
    ctx.send.assert_any_await(f"I couldn't send a private message to {user.display_name}. They may have DMs disabled.")
