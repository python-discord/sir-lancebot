import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.exts.fun.yodaify import Yodaify


@pytest.mark.asyncio
@patch("bot.exts.fun.yodaify.Yodaify.yodaify", new_callable=AsyncMock)
async def test_yodaify_command_is_called(mock_yodaify):
    """
    Requirement 1: Bot-command
    When a user writes .yoda <text> it runs the function.
    """
    ctx = AsyncMock()

    # Simulate a user writing ".yodaify I am driving a car."
    await mock_yodaify(ctx, text="I am driving a car.")

    # Verify that the command was indeed called with the expected arguments
    mock_yodaify.assert_awaited_once_with(ctx, text="I am driving a car.")


async def yodaify_conversion_helper(text, converted_text):
    """
    Requirement 5 Format: The returned text should have the format object-subject-verb.
    Requirement 7 Consistency: No words should be lost during the conversion.
    Requirement 8 Capitalization: The sentence should be capitalized correctly.
    """

    cog = Yodaify()

    mock_ctx = MagicMock()
    mock_ctx.author.display_name = "TestUser"
    mock_ctx.send = AsyncMock()
    mock_ctx.author.edit = AsyncMock()

    await cog.yodaify.callback(cog, mock_ctx, text=text)

    # Ensure a message was sent
    mock_ctx.send.assert_called_once()
    args, kwargs = mock_ctx.send.call_args
    sent_message = args[0]
    assert sent_message == converted_text, f"Unexpected sent message: {sent_message}"


@pytest.mark.asyncio
async def test_yodaify_conversion_1():

    await yodaify_conversion_helper("I like trains.", ">>> " + "Trains, I like.")


@pytest.mark.asyncio
async def test_yodaify_conversion_2():
    await yodaify_conversion_helper("I am driving a car.", ">>> " + "Driving a car, I am.")


@pytest.mark.asyncio
async def test_yodaify_conversion_3():
    await yodaify_conversion_helper("She likes my new van.", ">>> " + "My new van, she likes.")


@pytest.mark.asyncio
async def test_yodaify_conversion_4():
    await yodaify_conversion_helper("We should get out of here.", ">>> " + "Get out of here, we should.")


@pytest.mark.asyncio
async def test_yodaify_invalid_sentecne():
    """
    Requirement 6 Invalid sentence: If no changes to the format can be made, it should return: “Yodafication this doesn't need {username}!” + the original text.
    """
    await yodaify_conversion_helper("sghafuj fhaslkhglf ajshflka.", "Yodafication this doesn't need, TestUser!" + "\n>>> " + "sghafuj fhaslkhglf ajshflka.")


@pytest.mark.asyncio
async def test_yodaify_multiple_sentances():
    """
    Requirement 9 Multiple sentences:
    """
    await yodaify_conversion_helper("I like trains. I am driving a car. She likes my new van.", ">>> " + "Trains, I like. Driving a car, I am. My new van, she likes.")

