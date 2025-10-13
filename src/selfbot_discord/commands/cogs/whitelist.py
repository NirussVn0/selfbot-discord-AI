# Whitelist management cog for self-bot.

from __future__ import annotations

import yaml

from selfbot_discord.commands.base import Cog, CommandContext, CommandError, command


class WhitelistCog(Cog):
    VALID_FIELDS = {"user_ids", "guild_ids", "channel_ids"}

    @command("whitelist", description="Inspect or modify whitelist settings.")
    async def whitelist(self, ctx: CommandContext) -> None:
        if not ctx.args:
            raise CommandError("Usage: whitelist <show/add/rm/true/false> [field] [ids...]")

        action = ctx.args[0].lower()
        service = ctx.whitelist

        if action == "show":
            summary = yaml.safe_dump(service.summary(), sort_keys=False)
            message = await ctx.respond(f"```yaml\n{summary}\n```")
            await ctx.bot.schedule_ephemeral_cleanup(ctx.message, message, delay=5.0)
            return

        if action in {"true", "false"}:
            enabled = action == "true"
            changed = service.toggle(enabled)
            text = "Whitelist already in that state." if not changed else f"Whitelist enabled set to {enabled}."
            message = await ctx.respond(text)
            await ctx.bot.schedule_ephemeral_cleanup(ctx.message, message, delay=5.0)
            return

        if action in {"add", "rm"}:
            await self._handle_mutation(ctx, service, action)
            return

        raise CommandError(f"Unknown whitelist action '{action}'.")

    async def _handle_mutation(self, ctx: CommandContext, service, action: str) -> None:
        if len(ctx.args) < 3:
            raise CommandError("Usage: whitelist <add/rm> <user_ids|guild_ids|channel_ids> <id...>")

        field = ctx.args[1].lower()
        if field not in self.VALID_FIELDS:
            raise CommandError(f"Field must be one of: {', '.join(sorted(self.VALID_FIELDS))}")

        try:
            values = [int(value) for value in ctx.args[2:]]
        except ValueError as exc:
            raise CommandError("IDs must be integers.") from exc

        if action == "add":
            changes = service.add_entries(field, values)
            text = "No new IDs were added." if not changes else f"Added IDs to `{field}`: {', '.join(map(str, changes))}"
        else:
            changes = service.remove_entries(field, values)
            text = "No IDs were removed." if not changes else f"Removed IDs from `{field}`: {', '.join(map(str, changes))}"

        message = await ctx.respond(text)
        await ctx.bot.schedule_ephemeral_cleanup(ctx.message, message, delay=5.0)
