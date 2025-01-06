import nextcord
from nextcord.ext import commands


def is_in_guild():
    def predicate(ctx: commands.Context):
        return ctx.guild and ctx.guild.id == SERVER_ID

    return commands.check(predicate)


# is-a.dev
SUGGESTION_CHANNEL_ID = 1236200920317169695
MAINTAINER_ROLE_ID = 830875873027817484
SERVER_ID = 830872854677422150
COUNTING_CHANNEL_ID = 1006903455916507187
BOOSTER_ROLE_ID = 834807222676619325
POSITION_ROLE_ID = 1295386316464328806  # Role ID to place new roles under
STAFF_ROLE_ID = 1197475623745110109
PR_CHANNEL_ID = 1130858271620726784


# help forum
VIEW_GUILD_ID = 830872854677422150
VIEW_CHANNEL_ID = 1220286726711545926
USER_THREAD_LIMIT = 3

# Thread settings
VIEW_OPEN_LABEL = "Open Thread"
VIEW_CLOSE_LABEL = "Close Thread"

THREAD_MIN_CHAR = 35
THREAD_MIN_SUPPRESS_PREFIX = "?suppress"
THREAD_MIN_FAIL = f"Your message must be at least {THREAD_MIN_CHAR} characters long. Please provide more detail about the issue which you are facing."
THREAD_NAME = "Help Thread (member.name)"
THREAD_EMBED_TITLE = "**Please read this message before you make your first message.**"
THREAD_EMBED_RESOURCES = "- [Documentation](https://is-a.dev/docs)\n- [GitHub Repository](https://github.com/is-a-dev/register)\n- [FAQ](https://www.is-a.dev/docs/faq/)"
THREAD_EMBED_DESCRIPTION = "Hello member.mention,\n\nPlease describe your issue in as much detail as possible. If you would like to close this thread, click the button below.\n **Firstly we'd recommend you to go through the FAQ listed below.**\nIf your issue isn't listed in the FAQ then you can ask in this thread. "
THREAD_CLOSE_MSG = "This thread has been closed. If you have any further questions, feel free to open a new thread."
THREAD_CLOSE_DM = "Your thread has been closed. If you have any further questions, feel free to open a new thread."
THREAD_CLOSE_LOCK = True  # If True, the thread will be locked and closed. If False, the thread will only be closed.

SETUP_HELP_ALREADY = "This guild already has a help system set up."
SETUP_HELP_SUCCESS = "Successfully set up help system."



# celebrating cirno's power
SERVER_ID = 1281898369236602903