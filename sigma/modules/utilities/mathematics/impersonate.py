﻿import functools
from concurrent.futures import ThreadPoolExecutor

import discord
import markovify

from sigma.core.utilities.data_processing import user_avatar


async def impersonate(cmd, message, args):
    if not await cmd.bot.cool_down.on_cooldown(cmd.name, message.author):
        if args:
            if message.mentions:
                target = message.mentions[0]
            else:
                target = discord.utils.find(lambda x: x.name.lower() == ' '.join(args).lower(), message.guild.members)
        else:
            target = message.author
        if target:
            await cmd.bot.cool_down.set_cooldown(cmd.name, message.author, 20)
            init_embed = discord.Embed(color=0xbdddf4, title='💭 Hmm... Let me think...')
            init_message = await message.channel.send(embed=init_embed)
            chain_data = await cmd.db[cmd.db.db_cfg.database]['MarkovChains'].find_one({'UserID': target.id})
            if chain_data:
                if chain_data['Chain']:
                    total_string = ' '.join(chain_data['Chain'])
                    chain_function = functools.partial(markovify.Text, total_string)
                    with ThreadPoolExecutor() as threads:
                        chain = await cmd.bot.loop.run_in_executor(threads, chain_function)
                        sentence_function = functools.partial(chain.make_short_sentence, 500)
                        sentence = await cmd.bot.loop.run_in_executor(threads, sentence_function)
                    if not sentence:
                        response = discord.Embed(color=0xBE1931, title='😖 I could not think of anything...')
                    else:
                        response = discord.Embed(color=0xbdddf4)
                        response.set_author(name=target.name, icon_url=user_avatar(target))
                        response.add_field(name='💭 Hmm... something like...', value=sentence)
                else:
                    response = discord.Embed(color=0xBE1931, title=f'❗ {target.name}\'s chain has no data.')
            else:
                response = discord.Embed(color=0x696969)
                prefix = await cmd.bot.get_prefix(message)
                title = f'🔍 Chain Data Not Found For {target.name}'
                value = f'You can make one with `{prefix}collectchain @{target.name} #channel`!'
                response.add_field(name=title, value=value)
            await init_message.edit(embed=response)
        else:
            no_target = discord.Embed(color=0xBE1931, title='❗ No user targeted.')
            await message.channel.send(embed=no_target)
    else:
        timeout = await cmd.bot.cool_down.get_cooldown(cmd.name, message.author)
        on_cooldown = discord.Embed(color=0xccffff, title=f'❄ On cooldown for another {timeout} seconds.')
        await message.channel.send(embed=on_cooldown)
