import discord
from discord.ext import commands
from discord.ui import Button, View, Select
from database_controller import product_post, product_get, product_delete, converter, update_product, product_presentation, logging_bool_converter
from database_controller import get_selected_product, ticket_post, ticket_get, ticket_delete
from datetime import datetime
import asyncio
from random import randint
import os
from dotenv import load_dotenv
from payment_processing import create_a_bill, if_payment_is_done

load_dotenv('data/.env.prod')
env_prefix = 'prod_'

# load_dotenv('data/.env.test')
# env_prefix='test_'

# env_prefix = ''

in_order_status = {}
ticket = {}
view = {}
user_data = {}
counter = {}
admin_id = [519148522373644299, 439398320327098390]

desc = 'Тестовый бот-магазин'
ord_cat_counter = 3

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

orders_channel = int(os.getenv(env_prefix+'orders_channel'))
admin_channel = int(os.getenv(env_prefix+'admin_channel'))
customer_role_id = int(os.getenv(env_prefix+'customer_role_id'))
bot_key = os.getenv(env_prefix+'bot_key')

bot = commands.Bot(command_prefix='!', description=desc, intents=intents)


async def payment_timeout_counter(channel_id, ctx, user):
    await asyncio.sleep(180)
    
    answer = await if_payment_is_done(user_data[channel_id]['bill_id'])
                    
    if answer == 'Confirm':
        ctx.channel.id = channel_id
        await ctx.send('Канал не удалён из-за бездействия т.к пользователь оплатил заказ')
    
    else:
        if user_data[channel_id]['is_active'] is False:
            await idle_ticket_closure(channel_id)
            
            ctx.channel.id = orders_channel
            await ctx.send(f'<@{user}>, заказ закрыт из-за бездействия')
            
        else:
            print('Пользователь активен, канал не удалён')
    

async def idle_ticket_closure(channel, user=None):
    channel_object = bot.get_channel(channel)  
    print(channel_object.name,'is deleted')
    
    if user is not None:
        in_order_status[user] = 0
        
    await channel_object.delete()


def string_converter(input):
    if input == 'duration':
        return 'длительность'
    
    if input == 'with_logging':
        return 'с заходом на аккаунт'


def check(message):
    return message.author != bot.user


async def adding_info_gathering_text(ctx):
    """
    Function that gathers text part of 
    the info about the product that 
    admin is trying to add to the database 
    
    Takes:
        ctx(context) - context of the current
        chat that admin is using
    
    Returns:
        result(dict) - contains the name,
        description and the price
        of the product
    """
    global result
    
    command_channel = ctx.channel.id
    
    result = {}
    
    if command_channel != admin_channel:
        return
    
    view = View()
    
    await ctx.send('Введите название товара: (exit для прекращения добавления товара)', view=view)
    name_message = await bot.wait_for('message', check=check)
    
    if name_message.content == 'exit':
        return 'exit'
    
    if name_message is None:
        return
    
    result.update({'name': name_message.content})
    
    await ctx.send('Введите описание товара:', view=view)
    desc_message = await bot.wait_for('message', check=check)
    
    if desc_message.content == 'exit':
        return 'exit'
    
    if desc_message is None:
        return
    
    result.update({'description': desc_message.content})
        
    async def price_check():
        await ctx.send('Введите цену товара (целое число) (exit для прекращения добавления товара):', view=view)
        price_message = await bot.wait_for('message', check=check)
        
        if price_message.content == 'exit':
            return
        
        if price_message is None:
            return 
    
        try:
            result.update({'price': int(price_message.content)})
            
        except:
            await ctx.send('Некорректное значение, введите ещё раз:')
            await price_check()
    
    await price_check()
    
    await ctx.send('Введите сообщение после оплаты: (exit для прекращения добавления товара)', view=view)
    after_payment_message = await bot.wait_for('message', check=check)

    if after_payment_message.content == 'exit':
        return 'exit'
    
    if after_payment_message is None:
        return 

    result.update({'message_after_payment': after_payment_message.content})
    
    return result


async def update_info_gathering_text(ctx):
    """
    Function that gathers text part of 
    the info about the product that 
    admin is trying to update in the database 
    
    Takes:
        ctx(context) - context of the current
        chat that admin is using
    
    Returns:
        result(dict) - contains the name,
        description and the price
        of the product
    """
    global result
    
    command_channel = ctx.channel.id
    
    result = {}
    
    if command_channel != admin_channel:
        return

    view = View()
    
    await ctx.send('Введите название товара: (skip для пропуска)', view=view)
    name_message = await bot.wait_for('message', check=check)
    
    if name_message is None:
        return
    
    if name_message.content != 'skip':
        result.update({'name': name_message.content})
    
    await ctx.send('Введите описание товара: (skip для пропуска)', view=view)
    desc_message = await bot.wait_for('message', check=check)
    
    if desc_message is None:
        return
    
    if desc_message.content != 'skip':
        result.update({'description': desc_message.content})
        
    async def price_check():
        await ctx.send('Введите цену товара (целое число): (skip для пропуска)', view=view)
        price_message = await bot.wait_for('message', check=check)
        
        if price_message is None:
            return 
    
        try:
            if price_message.content != 'skip':
                result.update({'price': int(price_message.content)})
        except:
            await ctx.send('Некорректное значение, введите ещё раз:')
            await price_check()
    
    await price_check()
    
    await ctx.send('Введите сообщение после оплаты: (skip для пропуска)', view=view)
    after_payment_message = await bot.wait_for('message', check=check)

    if after_payment_message is None:
        return 
    
    if after_payment_message.content != 'skip':
        result.update({'message_after_payment': after_payment_message.content})
    
    return result

    
async def adding_info_gathering_buttons(ctx, result_input):    
    """
    Function that gathers text part of 
    the info about the product that 
    admin is trying to add to the database 
    
    Takes:
        ctx(context) - context of the current
        chat that admin is using
        
    Returns:
        result(dict) - contains the name,
        description, price and message
        after payment of the product
    """ 
     
    view = View()
    
    result = result_input
    
    global output
    output = None
    
    async def red_button_callback(interaction):
        global result
        result.update({'with_logging': False})
        await interaction.message.delete()
    
    async def green_button_callback(interaction):
        global result
        result.update({'with_logging': True})
        await interaction.message.delete()
        
    async def cancel_button_callback(interaction):  
        global output
        
        output = 'Cease'
        
        await interaction.response.defer()
        
    green_button = Button(label='Со входом', style=discord.ButtonStyle.green, custom_id='with_logging')
    red_button = Button(label='Без входа', style=discord.ButtonStyle.red, custom_id='without_logging')
    cancel_button = Button(label='Прекратить добавление', style=discord.ButtonStyle.grey, custom_id='cancel_adding')
    
    cancel_button.callback = cancel_button_callback
    green_button.callback = green_button_callback
    red_button.callback = red_button_callback
    
    view.add_item(green_button)
    view.add_item(red_button)
    view.add_item(cancel_button)

    await ctx.send('Выберите опцию:', view=view)
    
    await bot.wait_for('interaction')
    
    if output != 'Cease':
    
        view.clear_items()
        
        async def duration_input_callback(interaction):
            global result
            selected_value = interaction.data['values'][0]

            if selected_value == '1':
                result.update({'duration': int(selected_value)})
            elif selected_value == '3':
                result.update({'duration': int(selected_value)})
            elif selected_value == '6':
                result.update({'duration': int(selected_value)})
            elif selected_value == '12':
                result.update({'duration': int(selected_value)})
            elif selected_value == 'None':
                result.update({'duration': None})
            elif selected_value == 'Cancel':
                pass
                
            await interaction.message.delete()

        duration_options = Select(custom_id='duration_options', options=[
            discord.SelectOption(label='1 месяц', value='1'),
            discord.SelectOption(label='3 месяца', value='3'),
            discord.SelectOption(label='6 месяцев', value='6'),
            discord.SelectOption(label='12 месяцев', value='12'),
            discord.SelectOption(label='Навсегда', value='None'),
            discord.SelectOption(label='Отменить заказ', value='Cancel')
        ])
        
        duration_options.callback = duration_input_callback

        view.add_item(duration_options)
        
        await ctx.send('Выберите длительность товара:', view=view)
        
        await bot.wait_for('interaction')
        
    return result

    
async def update_info_gathering_buttons(ctx, result_input):    
    """
    Function that gathers text part of 
    the info about the product that 
    admin is trying to update in the database 
    
    Takes:
        ctx(context) - context of the current
        chat that admin is using
        
        result_input(dict) - previously
        collected data from user
        
    Returns:
        result(dict) - contains the info
        about the product
    """ 
     
    view = View()
    
    result = result_input
    
    async def red_button_callback(interaction):
        global result
        result.update({'with_logging': False})
        await interaction.message.delete()
    
    async def green_button_callback(interaction):
        global result
        result.update({'with_logging': True})
        await interaction.message.delete()
        
    async def grey_button_callback(interaction):
        await interaction.message.delete()
        
    green_button = Button(label='Со входом', style=discord.ButtonStyle.green, custom_id='with_logging')
    red_button = Button(label='Без входа', style=discord.ButtonStyle.red, custom_id='without_logging')
    grey_button = Button(label='Пропуск', style=discord.ButtonStyle.gray, custom_id='logging_skip')
    
    green_button.callback = green_button_callback
    red_button.callback = red_button_callback
    grey_button.callback = grey_button_callback
    
    view.add_item(green_button)
    view.add_item(red_button)
    view.add_item(grey_button)
    
    await ctx.send('Выберите опцию:', view=view)
    
    await bot.wait_for('interaction')
    
    view.remove_item(green_button)
    view.remove_item(red_button)
    view.remove_item(grey_button)
    
    async def duration_input_callback(interaction):
        global result
        selected_value = interaction.data['values'][0]

        if selected_value == '1':
            result.update({'duration': int(selected_value)})
        elif selected_value == '3':
            result.update({'duration': int(selected_value)})
        elif selected_value == '6':
            result.update({'duration': int(selected_value)})
        elif selected_value == '12':
            result.update({'duration': int(selected_value)})
        elif selected_value == 'None':
            result.update({'duration': None})
        elif selected_value == 'Skip':
            pass
            
        await interaction.message.delete()

    duration_options = Select(custom_id='duration_options', options=[
        discord.SelectOption(label='1 месяц', value='1'),
        discord.SelectOption(label='3 месяца', value='3'),
        discord.SelectOption(label='6 месяцев', value='6'),
        discord.SelectOption(label='12 месяцев', value='12'),
        discord.SelectOption(label='Навсегда', value='None'),
        discord.SelectOption(label='Пропустить', value='skip')
    ])
    
    duration_options.callback = duration_input_callback

    view.add_item(duration_options)
    
    await ctx.send('Выберите длительность товара:', view=view)
    
    await bot.wait_for('interaction')
    
    return result


@bot.event
async def on_ready():
    print (f'logged in as {bot.user}, id: {bot.user.id}, {bot_key}')
    print ('-------')


async def add_a_product(ctx):
    
    result = await adding_info_gathering_text(ctx)
    
    if result == 'exit':
        
        await ctx.send('Добавление товара отменено!')
        return 
    
    result = await adding_info_gathering_buttons(ctx, result)
    
    if len(list(result.keys())) == 6:
    
        product_post(result)
        
        await ctx.send(
f"""Товар добавлен!
__________""")
    
        product = product_get(get_last=True)
        
        await ctx.send(
f"""ID: {product[0]},
Название товара: {product[1]},
Описание товара: {product[2]},
Длительность товара: {converter(product[3])},
С заходом на аккаунт: {converter(product[4])},
Скрыт: {converter(product[5])},
Сообщение после оплаты: {product[6]},
Цена: {product[7]},
Дата создания: {product[8]}""")
    
    else:
        await ctx.send('Добавление товара отменено!')
    
    
async def get_products(ctx):

    products = product_get()
    
    c = 1
    
    view=View()
    view_c=View()
    
    async def create_buttons(product):
        
        async def delete_button_callback(interaction, product):
            product_id = product[0]
            product_delete(product[0])
            await interaction.message.edit(content=f'Запись с ID {product[0]} удалена', view=view_c)
        
        async def block_button_callback(interaction, product):
            product_id = product[0]
            update_product(id=product_id, if_unblocking=True)
            await interaction.message.edit(content=f'Запись с ID {product[0]} скрыта/возвращена', view=view_c)
            
        async def edit_button_callback(interaction, product):
            await interaction.response.defer()
            
            product_id = product[0]
            
            result = await update_info_gathering_text(ctx)
            result = await update_info_gathering_buttons(ctx, result)
            
            update_product(id=product_id, if_unblocking=False, update_content=result)
            
            await ctx.send(
f"""Товар с ID {product_id} изменён!
__________
""")
            
            product = product_get(id=product_id)[0]

            await ctx.send(
f"""ID: {product[0]},
Название товара: {product[1]},
Описание товара: {product[2]},
Длительность товара: {converter(product[3])},
С заходом на аккаунт: {converter(product[4])},
Скрыт: {converter(product[5])},
Сообщение после оплаты: {product[6]},
Цена: {product[7]}""")

        delete_button = Button(label='Удалить', style=discord.ButtonStyle.red, custom_id=f'delete_{product[0]}')
        edit_button = Button(label='Изменить', style=discord.ButtonStyle.primary, custom_id=f'edit_{product[0]}')
        block_button = Button(label='Скрыть/Вернуть для покупателей', style=discord.ButtonStyle.gray, custom_id=f'hide_{product[0]}')
        
        delete_button.callback = lambda b: delete_button_callback(b, product=product)
        block_button.callback = lambda b: block_button_callback(b, product=product)
        edit_button.callback = lambda b: edit_button_callback(b, product=product)
        
        view.add_item(delete_button)
        view.add_item(edit_button)
        view.add_item(block_button)
    
    await ctx.send('Пожалуйста, не нажимайте кнопку изменения товара, пока не отрисуются все товары из базы данных')
    for product in products:
        
        c_product = list(product)
        
        await create_buttons(c_product)
        
        c+=1
        
        await ctx.send(
(f"""ID: {product[0]},
Название товара: {product[1]},
Описание товара: {product[2]},
Длительность товара: {converter(product[3])},
С заходом на аккаунт: {converter(product[4])},
Скрыт: {converter(product[5])},
Сообщение после оплаты: {product[6]},
Цена: {product[7]},
Дата создания: {product[8]}"""), 
                        view=view)
        
        view.clear_items()


async def buttons_creation(item, ctx, label, channel, view, input_str):    
    button = Button(label=label, style=discord.ButtonStyle.blurple, custom_id=f'ticket_{input_str}_{item}_{channel}_{randint(0,100000)}')
    async def button_callback(interaction, item):
        ctx.channel.id = channel
        ticket[channel].update({input_str: item})
        await interaction.message.edit(content=f'Вы выбрали {string_converter(input_str)}: {converter(item)}', view=View())
        
    button.callback = lambda b: button_callback(b, item=item)
    view.add_item(button)


async def order_info_gathering(ctx, channel, products_dict):
    view = View()
    ctx_author = ctx.author.id

    cancel_button = Button(label='Отмена заказа', style=discord.ButtonStyle.gray, custom_id='order_canceling')

    async def cancel_button_callback(interaction, ctx_author, ctx, channel):
        in_order_status[f"{ctx_author} pip"] = False
        in_order_status[ctx_author] = 0
        
        await interaction.response.defer()
        
        channel_object = bot.get_channel(channel)  
        
        await channel_object.delete()
        
        ctx.channel.id = orders_channel
        
        await ctx.send (f'<@{ctx.author.id}> заказ отменён!')
    
    cancel_button.callback = lambda b: cancel_button_callback(b, ctx_author, ctx=ctx, channel=channel)
    
    ctx.channel.id = channel
    
    def interaction_check(interaction):
        return interaction.channel_id == channel
    
    name = ticket[channel]['name']
    duration_list = products_dict[name]['duration']
    
    for item in duration_list:
        await buttons_creation(item=item, ctx=ctx, channel=channel, label=converter(item), view=view, input_str='duration')

    view.add_item(cancel_button)    
        
    await ctx.send('Длительность: ', view=view)
    
    try:
        interaction = await bot.wait_for('interaction', check=interaction_check, timeout=90)

        user = ctx.author.id
        
    except asyncio.TimeoutError:
        await idle_ticket_closure(channel, ctx_author, ctx)

    if in_order_status[f"{ctx.author.id} pip"] == True:
    
        view.clear_items()
        ctx.channel.id = channel
        
        with_logging_list = products_dict[name]['with_logging']
        
        for item in with_logging_list:
            existing_buttons = []
            if list(item.values())[0] == ticket[channel]['duration'] and list(item.keys())[0] not in existing_buttons:
                
                existing_buttons.append(list(item.keys())[0])
                await buttons_creation(item=list(item.keys())[0], ctx=ctx, channel=channel, label=logging_bool_converter(list(item.keys())[0]), view=view, input_str='with_logging')
        
        view.add_item(cancel_button)    
        
        await ctx.send('Со входом на аккаунт: ', view=view)
        
    try:
        interaction = await bot.wait_for('interaction', check=interaction_check, timeout=90)
    
    except asyncio.TimeoutError:
        await idle_ticket_closure(channel, ctx_author)
        ctx.channel.id = orders_channel
        await ctx.send(f'<@{ctx.author.id}>, канал удалён из-за бездействия')
                
    if in_order_status[f"{ctx.author.id} pip"] == True:
        
        view.clear_items()
        
        async def show_result_button_callback(interaction, name, duration, with_logging):
            ctx.channel.id = channel
            product = get_selected_product(name, duration, with_logging)
            
            item = {}
            
            item['product_id'] = product[0]
            item['product_name'] = product[1]
            item['product_price'] = product[7]
            item['product_message_after_payment'] = product[6]
            item['ticket_channel_id'] = channel
            
            ticket_post(item)
            user_data[ctx.channel.id]['ticket_info'] = ticket_get(get_last=True)
            
            await ctx.send(
    f"""Ваш заказ:
    ______________________________
    Название товара: {product[1]},
    Описание товара: {product[2]},
    Длительность товара: {converter(product[3])},
    С заходом на аккаунт: {converter(product[4])},
    Цена: {product[7]} рублей"""
                        )
            
            await interaction.message.edit(content=f'Вы успешно оформили тикет', view=View())
            
        show_result_button = Button(label='Создать тикет', style=discord.ButtonStyle.blurple, custom_id=f'ticket_show_{channel}')
        
        show_result_button.callback = lambda b: show_result_button_callback(interaction=b, 
                                                    name = ticket[channel]['name'], 
                                                    duration = ticket[channel]['duration'],
                                                    with_logging = ticket[channel]['with_logging']
                                                    ) 
        
        view.add_item(show_result_button)
        
        ctx.channel.id = channel
        
        view.add_item(cancel_button)    
        
        await ctx.send("Для продолжения или отмены нажмите на кнопку: ", view=view)
        
    try:
        interaction = await bot.wait_for('interaction', check=interaction_check, timeout=90)
    
    except asyncio.TimeoutError:
        await idle_ticket_closure(channel, ctx_author)
        ctx.channel.id = orders_channel
        await ctx.send(f'<@{ctx.author.id}>, канал удалён из-за бездействия')
        
    if in_order_status[f"{ctx.author.id} pip"] == True:
        
        in_order_status[ctx.author.id] = 0
        
        view.clear_items()
        ctx.channel.id = channel
        
        await ctx.send(f'<@{admin_id[1]}>, заказ оформлен и готов к работе, покупатель - <@{ctx.author.id}>')
        
        bill = await create_a_bill(user_data[channel]['ticket_info'][3])
        
        user_data[channel]['bill_url'] = bill[0]
        user_data[channel]['bill_id'] = bill[1]
        
        user_data[channel]['is_blocked'] = True
        
        id = user_data[channel]['ticket_info'][0]
        message_after_payment = user_data[channel]['ticket_info'][4]
        
        await ctx.send(
f"""
--
Вот ваша ссылка для оплаты: {user_data[channel]["bill_url"]}
--
[Через 3 минуты откроется меню для подтверждения оплаты или вызова админа]
--
Примечание: при оплате счёта к сумме заказа будет добавлено 35 рублей - комиссия платёжного сервиса
--
"""
)
        
        await asyncio.sleep(180)
        
        asyncio.create_task(payment_timeout_counter(channel, ctx, ctx.author.id))
        user_data[channel]['is_active'] = False
        
        view=View()
        
        async def order_closing(view, channel):
            
            ctx.channel.id = channel
            
            async def close_order_button_callback(interaction):
                await interaction.response.defer()

            close_order_button = Button(label='Закрыть заказ', style=discord.ButtonStyle.red, custom_id=f'Close_order_{id}')
            close_order_button.callback = close_order_button_callback
            
            view.clear_items()
            view.add_item(close_order_button)
                    
            await ctx.send('Обработка заказа со стороны бота завершена. Нажмите кнопку, чтобы закрыть тикет', view=view)
            
            def admin_interaction_check(interaction):
                return interaction.user.id in admin_id and interaction.channel.id == channel
            
            interaction = await bot.wait_for('interaction', check=admin_interaction_check)
            
            if interaction:
                
                guild = ctx.guild
                channel_id = channel
                channel = bot.get_channel(channel_id)
                customer_role = discord.utils.get(guild.roles, id=customer_role_id) 

                in_order_status[ctx.author.id] = 0
                
                await channel.set_permissions(customer_role, send_messages=False)
                await channel.edit(name=f'completed{user_data[channel_id]["channel_num"]}')
                
                ctx.channel.id = channel_id
                
                await ctx.send('Заказ закрыт. Теперь здесь писать может только администратор')
                
                user_data[channel_id]['is_blocked'] = True
                user_data[channel_id]['is_over'] = True
                
                
        async def payment_submit_button_callback(interaction):
            user_data[channel]['is_active'] = True
            await interaction.response.defer()
            
            ctx.channel.id = channel
            
            if user_data[channel]['is_blocked'] == False:
                
                answer = await if_payment_is_done(user_data[channel]['bill_id'])
                    
                if answer == 'Confirm':
                    
                    ctx.channel.id = channel
                    
                    await ctx.send(f'<@{admin_id[1]}>, Платёж успешно принят системой')
                    await ctx.send(f'ID вашего тикета: {id}')
                    await ctx.send(
f"""
--
Ваше сообщение после оплаты:

{message_after_payment}
--
""")            

                    await order_closing(view, channel)
                    
                    user_data[channel]['is_blocked'] = True
                
                else:
                    ctx.channel.id = channel
                    
                    await ctx.send('Платёж не прошёл. Попробуйте ещё раз позже или свяжитесь с администратором' )

        
        async def call_admin_button_callback(interaction):
            user_data[channel]['is_active'] = True
            await interaction.response.defer()
            
            if user_data[channel]['is_blocked'] == False:
                
                ctx.channel.id = channel
                
                await ctx.send(f'<@{admin_id[1]}>, у покупателя <@{ctx.author.id}> проблемы с заказом')
                
                while True:
                    
                    try:
                    
                        message = await bot.wait_for('message', check=lambda m: m.content == '/payment_recieved' and m.channel.id == channel and m.author.id in admin_id, timeout=180)
                        
                        if message:
                            ctx.channel.id = channel
                            user_data[channel]['is_blocked'] = True
                            
                            await ctx.send(f'ID вашего тикета: {id}')
                            await ctx.send(
f"""
--
Ваше сообщение после оплаты:

{message_after_payment}
--
""")
                        
                            await order_closing(view, channel)
                        
                        break
                    
                    except asyncio.TimeoutError:
                        print(f'Channel {bot.get_channel(channel).name} has been inactive for 3 minutes')
            
        call_admin_button = Button(label='Проблемы с оплатой, позвать админа', style=discord.ButtonStyle.red, custom_id=f'call_admin_{id}')
        payment_submit_button = Button(label='Проверить оплату счёта', style=discord.ButtonStyle.green, custom_id=f'payment_sent_{id}')
        
        payment_submit_button.callback = payment_submit_button_callback
        call_admin_button.callback = call_admin_button_callback
        
        view.add_item(payment_submit_button)
        view.add_item(call_admin_button)
        
        ctx.channel.id = channel
        
        user_data[channel]['is_over'] = False
        user_data[channel]['is_blocked'] = False
        
        def interaction_check(interaction):
            return interaction.channel_id == channel
        
        message = await ctx.send(f'Выберите опцию:', view=view)
        counter = 0
        
        while True:
        
            try:
                await bot.wait_for('interaction', check=interaction_check, timeout=120)

            except asyncio.TimeoutError:
                
                try: 
                    if user_data[channel]['is_over'] == False:
                        bot.get_channel(channel)
                        counter+=1
                        
                        print(f'Interaction timed out {counter}th time in channel {channel}')
                        
                        view = View()
                        view.add_item(payment_submit_button)
                        view.add_item(call_admin_button)
                        ctx.channel.id = channel
                        
                        await message.edit(content='Выберите опцию:', view=view)
                        
                    else:
                        break
                
                except discord.errors.NotFound:
                    break
        
    
async def order_info_gathering_init(ctx, new_channel_id):
    ctx.channel.id = new_channel_id
    channel = ctx.channel.id
    
    ticket[channel] = {}
    view = View()
    
    products_dict, names_list = product_presentation()
    
    async def name_buttons_creation(item):
        
        button = Button(label=item, style=discord.ButtonStyle.blurple, custom_id=f'ticket_name_{item}_{channel}')
        
        async def button_callback(interaction, item, products_dict, ctx):
            ctx.channel.id = channel
            ticket[channel] = {'name': item}

            await interaction.message.edit(content=f'Вы выбрали товар {item}', view=View())
            await order_info_gathering(ctx, channel, products_dict)

        button.callback = lambda b: button_callback(b, item=item, products_dict=products_dict, ctx=ctx)
        view.add_item(button)
        
    for item in names_list:
        await name_buttons_creation(item)
        
    async def cancel_button_callback(interaction, ctx):
        await interaction.response.defer()
        in_order_status[ctx.author.id] = 0
        
        channel_object = bot.get_channel(new_channel_id)  
        
        await channel_object.delete()
        
        ctx.channel.id = orders_channel
        
        await ctx.send(f'<@{ctx.author.id}> заказ отменён!')
    
    cancel_button = Button(label='Отменить заказ', style=discord.ButtonStyle.gray, custom_id=f'delete_ticket_from_name{ctx.channel.id}')
    
    cancel_button.callback = lambda b: cancel_button_callback(b, ctx)
    
    view.add_item(cancel_button)
        
    await ctx.send('Выберите название продукта: ', view=view)
    
    def interaction_check(interaction):
        return interaction.channel_id == ctx.channel.id
    
    try:
        interaction = await bot.wait_for('interaction', check=interaction_check, timeout=90)
    
    except asyncio.TimeoutError:
        await idle_ticket_closure(channel, ctx.author.id)
        ctx.channel.id = orders_channel
        await ctx.send(f'<@{ctx.author.id}>, канал удалён из-за бездействия')
        
        
async def order_creation(ctx):
    global ord_cat_counter
    
    if in_order_status[ctx.author.id] == 0:
        in_order_status[ctx.author.id] = 1
        guild = ctx.guild
        category = discord.utils.get(guild.categories, name=f'Orders with payment #{ord_cat_counter}')
        
        if category:
        
            text_channel_count = sum(1 for channel in category.channels if isinstance(channel, discord.TextChannel))
            
            if text_channel_count >= 45:
                ord_cat_counter+=1
                category = await guild.create_category(name=f'Orders with payment #{ord_cat_counter}')
                
        else: 
            ord_cat_counter+=1
            category = await guild.create_category(name=f'Orders with payment #{ord_cat_counter}')
        
        bot_role = discord.utils.get(ctx.guild.roles, name="Eshop-bot")
        admin_role_1 = discord.utils.get(guild.roles, id=1077905856164794394)
        admin_role_2 = discord.utils.get(guild.roles, id=1077905856164794395)
        admin_role_3 = discord.utils.get(guild.roles, id=1077905856181567599)
            
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            ctx.author: discord.PermissionOverwrite(read_messages=True),
            admin_role_1: discord.PermissionOverwrite(read_messages=True),
            admin_role_2: discord.PermissionOverwrite(read_messages=True),
            admin_role_3: discord.PermissionOverwrite(read_messages=True),
            bot_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel_num = randint(1, 999999)
        
        new_channel = await guild.create_text_channel('order'+'0'*(6-len(str(channel_num)))+str(channel_num), 
                                                      overwrites=overwrites, 
                                                      category=category)
        new_channel_id = new_channel.id
        
        user_data[new_channel_id] = {}
        user_data[new_channel_id]['channel_num'] = channel_num
        
        ctx.channel.id = orders_channel

        await ctx.send(
f"""
<@{ctx.author.id}>, создали комнату для заказа: {new_channel.mention}
--
Важно! Канал автоматически удалится, а заказ закроется, если вы в течение 90 секунд не будете выполнять никаких действий
""",)
        
        await order_info_gathering_init(ctx, new_channel_id)

    else:
        ctx.channel.id = orders_channel
        
        await ctx.send(content=f'Извините, <@{ctx.author.id}> у вас уже есть активный заказ. Завершите его или закройте, чтобы создать новый')


@bot.command()
async def order(ctx):  
    """
    Сommand that creates new 
    text channel for user to order
    """

    orders_channel_object = bot.get_channel(orders_channel)
    
    if ctx.channel.name != orders_channel_object.name:
        return
    
    try:
        if in_order_status[ctx.author.id] == 0:
            in_order_status[f"{ctx.author.id} pip"] = True
            await order_creation(ctx)
        
        else:
            ctx.channel.id = orders_channel
            
            await ctx.send (f'Извините, <@{ctx.author.id}> у вас уже есть активный заказ. Завершите его или закройте, чтобы создать новый')
   
    except:
        in_order_status[ctx.author.id] = 0
        in_order_status[f"{ctx.author.id} pip"] = True
        
        await order_creation(ctx)
        
    
@bot.command()
async def apanel(ctx):
    
    if ctx.channel.id != admin_channel:
        return
    
    view=View()
    
    async def get_products_button_callback(interaction, ctx):
        await interaction.response.defer()
        await get_products(ctx)

    get_products_button = Button(label='Посмотреть товары', style=discord.ButtonStyle.blurple, custom_id='get_products_admin')
    
    get_products_button.callback = lambda b: get_products_button_callback(b, ctx=ctx)
    
    view.add_item(get_products_button)    
    
    async def add_a_product_button_callback(interaction, ctx):
        await interaction.response.defer()
        await add_a_product(ctx)

    add_a_product_button = Button(label='Добавить товар', style=discord.ButtonStyle.blurple, custom_id='add_a_product_admin')
    
    add_a_product_button.callback = lambda b: add_a_product_button_callback(b, ctx=ctx)
    
    view.add_item(add_a_product_button)   
    
    async def get_products_number_button_callback(interaction):
        await interaction.response.defer()
        products_number = product_get(if_counting=True)
        await ctx.send(f"Количество товаров в базе данных: {products_number}")

    get_products_number_button = Button(label='Посмотреть количество товаров', style=discord.ButtonStyle.blurple, custom_id='get_products_number')
    
    get_products_number_button.callback = get_products_number_button_callback
    
    view.add_item(get_products_number_button)     
    
    async def clear_in_order_status_button_callback(interaction):
        global in_order_status
        await interaction.response.defer()
        
        in_order_status = {}

        await ctx.send('Все пользователи теперь могут делать новый заказ')

    clear_in_order_status_button = Button(label='Очистить статус "Делает заказ" у всех пользователей', 
                                          style=discord.ButtonStyle.blurple, 
                                          custom_id='clear_users_inorder_status')
    
    clear_in_order_status_button.callback = clear_in_order_status_button_callback
    
    view.add_item(clear_in_order_status_button)   
    
    await ctx.send('Выберите опцию:', view=view)    


@bot.command()
async def remake_orders_channel(ctx):
    global orders_channel
    channel = ctx.channel.id
    
    if ctx.author.id in admin_id:
        
        await ctx.send('Напишите "Да" для подтверждения операции')
        
        def admin_message_check(message):
            return message.author.id in admin_id
        
        message = await bot.wait_for('message', check = admin_message_check)
        
        if message.content == 'Да': 
            orders_channel = channel
            
            await ctx.send('Теперь это канал для заказов')
            

@bot.command()
async def remake_admin_channel(ctx):
    global admin_channel
    channel = ctx.channel.id
    
    if ctx.author.id in admin_id:
        
        await ctx.send('Аккуратнее! Вы изменяете канал для работы с админ-панелью. Убедитесь, что здесь нет лишних пользователей')
        await ctx.send('---')
        await ctx.send('Напишите "Да" для подтверждения операции')
        
        def admin_message_check(message):
            return message.author.id in admin_id
        
        message = await bot.wait_for('message', check = admin_message_check)
        
        if message.content == 'Да': 
            admin_channel = channel
            
            await ctx.send('Теперь это канал для работы с админ-панелью')

bot.run(bot_key)