from collections.abc import Sequence

from discord import Embed, Interaction, Member, Message, Reaction
from discord.abc import User
from discord.ext.commands import Context, Paginator
from pydis_core.utils.logging import get_logger
from pydis_core.utils.pagination import EmptyPaginatorEmbedError, LinePaginator as _LinePaginator, PaginationEmojis

from bot.constants import Emojis

PAGINATION_EMOJI = PaginationEmojis(delete=Emojis.trashcan)

log = get_logger(__name__)


class LinePaginator(_LinePaginator):
    """A class that aids in paginating code blocks for Discord messages."""

    @classmethod
    async def paginate(
        cls,
        lines: list[str],
        ctx: Context | Interaction,
        embed: Embed,
        prefix: str = "",
        suffix: str = "",
        max_lines: int | None = None,
        max_size: int = 500,
        scale_to_size: int = 4000,
        empty: bool = True,
        restrict_to_user: User | None = None,
        timeout: int = 300,
        footer_text: str | None = None,
        url: str | None = None,
        exception_on_empty_embed: bool = False,
        reply: bool = False,
        allowed_roles: Sequence[int] | None = None,
    ) -> Message | None:
        """
        Use a paginator and set of reactions to provide pagination over a set of lines.

        Acts as a wrapper for the super class' `paginate` method to provide the pagination emojis by default.
        Consult the super class's `paginate` method for detailed information.
        """
        return await super().paginate(
            pagination_emojis=PAGINATION_EMOJI,
            lines=lines,
            ctx=ctx,
            embed=embed,
            prefix=prefix,
            suffix=suffix,
            max_lines=max_lines,
            max_size=max_size,
            scale_to_size=scale_to_size,
            empty=empty,
            restrict_to_user=restrict_to_user,
            timeout=timeout,
            footer_text=footer_text,
            url=url,
            exception_on_empty_embed=exception_on_empty_embed,
            reply=reply,
            allowed_roles=allowed_roles,
        )


class ImagePaginator(Paginator):
    """
    Helper class that paginates images for embeds in messages.

    Close resemblance to LinePaginator, except focuses on images over text.

    Refer to ImagePaginator.paginate for documentation on how to use.
    """

    def __init__(self, prefix: str = "", suffix: str = ""):
        super().__init__(prefix, suffix)
        self._current_page = [prefix]
        self.images = []
        self._pages = []

    def add_line(self, line: str = "", *, empty: bool = False) -> None:
        """
        Adds a line to each page, usually just 1 line in this context.

        If `empty` is True, an empty line will be placed after a given `line`.
        """
        if line:
            self._count = len(line)
        else:
            self._count = 0
        self._current_page.append(line)
        self.close_page()

    def add_image(self, image: str | None = None) -> None:
        """Adds an image to a page given the url."""
        self.images.append(image)

    @classmethod
    async def paginate(cls, pages: list[tuple[str, str]], ctx: Context, embed: Embed,
                       prefix: str = "", suffix: str = "", timeout: float = 300,
                       exception_on_empty_embed: bool = False) -> None:
        """
        Use a paginator and set of reactions to provide pagination over a set of title/image pairs.

        `pages` is a list of tuples of page title/image url pairs.
        `prefix` and `suffix` will be prepended and appended respectively to the message.

        When used, this will send a message using `ctx.send()` and apply a set of reactions to it.
        These reactions may be used to change page, or to remove pagination from the message.

        Note: Pagination will be removed automatically if no reaction is added for `timeout` seconds,
              defaulting to five minutes (300 seconds).

        >>> embed = Embed()
        >>> embed.set_author(name="Some Operation", url=url, icon_url=icon)
        >>> await ImagePaginator.paginate(pages, ctx, embed)
        """
        def check_event(reaction_: Reaction, member: Member) -> bool:
            """Checks each reaction added, if it matches our conditions pass the wait_for."""
            return all((
                # Reaction is on the same message sent
                reaction_.message.id == message.id,
                # The reaction is part of the navigation menu
                # Note: DELETE_EMOJI is a string and not unicode
                str(reaction_.emoji) in PAGINATION_EMOJI.model_dump().values(),
                # The reactor is not a bot
                not member.bot
            ))

        paginator = cls(prefix=prefix, suffix=suffix)
        current_page = 0

        if not pages:
            if exception_on_empty_embed:
                log.exception("Pagination asked for empty image list")
                raise EmptyPaginatorEmbedError("No images to paginate")

            log.debug("No images to add to paginator, adding '(no images to display)' message")
            pages.append(("(no images to display)", ""))

        for text, image_url in pages:
            paginator.add_line(text)
            paginator.add_image(image_url)

        embed.description = paginator.pages[current_page]
        image = paginator.images[current_page]

        if image:
            embed.set_image(url=image)

        if len(paginator.pages) <= 1:
            await ctx.send(embed=embed)
            return None

        embed.set_footer(text=f"Page {current_page + 1}/{len(paginator.pages)}")
        message = await ctx.send(embed=embed)

        for emoji in PAGINATION_EMOJI.model_dump().values():
            await message.add_reaction(emoji)

        while True:
            # Start waiting for reactions
            try:
                reaction, user = await ctx.bot.wait_for("reaction_add", timeout=timeout, check=check_event)
            except TimeoutError:
                log.debug("Timed out waiting for a reaction")
                break  # We're done, no reactions for the last 5 minutes

            # Deletes the users reaction
            await message.remove_reaction(reaction.emoji, user)

            # Delete reaction press - [:trashcan:]
            if str(reaction.emoji) == PAGINATION_EMOJI.delete:  # Note: DELETE_EMOJI is a string and not unicode
                log.debug("Got delete reaction")
                return await message.delete()

            # First reaction press - [:track_previous:]
            if reaction.emoji == PAGINATION_EMOJI.first:
                if current_page == 0:
                    log.debug("Got first page reaction, but we're on the first page - ignoring")
                    continue

                current_page = 0
                reaction_type = "first"

            # Last reaction press - [:track_next:]
            if reaction.emoji == PAGINATION_EMOJI.last:
                if current_page >= len(paginator.pages) - 1:
                    log.debug("Got last page reaction, but we're on the last page - ignoring")
                    continue

                current_page = len(paginator.pages) - 1
                reaction_type = "last"

            # Previous reaction press - [:arrow_left: ]
            if reaction.emoji == PAGINATION_EMOJI.left:
                if current_page <= 0:
                    log.debug("Got previous page reaction, but we're on the first page - ignoring")
                    continue

                current_page -= 1
                reaction_type = "previous"

            # Next reaction press - [:arrow_right:]
            if reaction.emoji == PAGINATION_EMOJI.right:
                if current_page >= len(paginator.pages) - 1:
                    log.debug("Got next page reaction, but we're on the last page - ignoring")
                    continue

                current_page += 1
                reaction_type = "next"

            # Magic happens here, after page and reaction_type is set
            embed.description = paginator.pages[current_page]

            image = paginator.images[current_page] or None
            embed.set_image(url=image)

            embed.set_footer(text=f"Page {current_page + 1}/{len(paginator.pages)}")
            log.debug(f"Got {reaction_type} page reaction - changing to page {current_page + 1}/{len(paginator.pages)}")

            await message.edit(embed=embed)

        log.debug("Ending pagination and clearing reactions...")
        await message.clear_reactions()
        return None
