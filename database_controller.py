import sqlalchemy as db
from database_models import metadata, products, ticket
from datetime import datetime
from random import randint
import os

db_url = "sqlite:///data/discord_Eshop.db"

engine = db.create_engine(db_url, echo=True)
conn = engine.connect()
metadata.create_all(engine)

def converter(input):
    if input == True and type(input) != int:
        return 'Да'
    elif input == False:
        return 'Нет'
    elif input == None:
        return 'Без ограничений'
    elif input == 1:
        return '1 месяц'
    elif input == 3:
        return '3 месяца'
    elif type(input) == int:
        return f'{input} месяцев'
    else:
        return 'Некорректное значение'
    
def logging_bool_converter(input):
    if input == True:
        return 'Со входом'
    elif input == False:
        return 'Без входа'
    

def product_post(item):
    product_insertion = products.insert().values(
                name=item['name'],
                description=item['description'],
                duration=item['duration'],
                with_logging=item['with_logging'],
                is_blocked=False,
                message_after_payment=item['message_after_payment'],
                price=item['price'],
                creation_date=datetime.now().strftime("%D, %H:%M")
            )
    
    conn.execute(product_insertion)
    conn.commit()

# dblist = database_autofill()
# for item in dblist:
#     product_post(item)

def get_selected_product(name, duration, with_logging):
    
    select_query = db.select(products).where(products.c.name == name, products.c.duration == duration, products.c.with_logging == with_logging)
    
    rows = conn.execute(select_query).fetchall()
    
    return rows[0]
    
  
def product_get(id=None, get_last=False, if_counting=False):    
    select_query = db.select(products)
    result = []
    
    if id is not None:
        select_query = select_query.where(products.c.id == id)
        
    rows = conn.execute(select_query).fetchall()
    
    for row in rows:
        result.append(row)
    
    if get_last == True:
        return result[len(result)-1]
    
    elif if_counting == True:
        return len(rows)
    
    else:
        return result


def update_product(update_content=None, id=None, if_unblocking=False, if_counting=False):
    item = product_get(id)[0]
    if if_unblocking == False:
        print(item[8])
        item = {
            'name':item[1],
            'description':item[2],
            'duration':item[3],
            'with_logging':item[4],
            'is_blocked':item[5],
            'message_after_payment':item[6],
            'price':item[7],
            'creation_date':item[8]
            }
        item.update(update_content)
        item = list(item.values())
        print(item)
        update_query = db.update(products).where(products.c.id == id).values(
            name=item[0],
            description=item[1],
            duration=item[2],
            with_logging=item[3],
            is_blocked=item[4],
            message_after_payment=item[5],
            price=item[6],
            creation_date=item[7]
            )
    
    else:
        update_query = db.update(products).where(products.c.id == id).values(is_blocked = not item[5])
    
    conn.execute(update_query)
    conn.commit()


def product_delete(id):
    delete_query = db.delete(products).where(products.c.id == id)
    conn.execute(delete_query)
    conn.commit()
    

def product_presentation():
    select_query = db.select(products)

    names = {}
    
    rows = conn.execute(select_query).fetchall()
    
    for row in rows:
        names.update({row[1]: {'duration': [], 'with_logging': []}})
        
    names_list = list(names.keys())   
    
    for name in names_list:
        for row in rows:
            if row[1] == name:
                names[row[1]]['duration'].append(row[3])
                names[row[1]]['with_logging'].append({row[4]: row[3]})
                
    for item in names_list:
        names[item]['duration'] = list(set(names[item]['duration']))
        names[item]['with_logging'] = (names[item]['with_logging'])
    
    for item in names_list:
        try:
            names[item]['duration'].sort()
        except:
            names[item]['duration'].pop(names[item]['duration'].index(None))
            names[item]['duration'].sort()
            names[item]['duration'].append(None)
    
    return names, names_list


def ticket_post(item):
    ticket_insertion = ticket.insert().values(
                product_id=item['product_id'],
                product_name=item['product_name'],
                product_price=item['product_price'],
                product_message_after_payment=item['product_message_after_payment'],
                ticket_channel_id=item['ticket_channel_id']
            )
    
    conn.execute(ticket_insertion)
    conn.commit()
    

def ticket_delete(id):
    delete_query = db.delete(ticket).where(products.c.id == id)
    conn.execute(delete_query)
    conn.commit()
    

def ticket_get(id=None, get_last=False):
    select_query = db.select(ticket)
    result = []
        
    if id is not None:
        select_query = select_query.where(products.c.id == id)    
        
    rows = conn.execute(select_query).fetchall()

    for row in rows:
        result.append(row)
    
    if get_last == True:
        return result[len(result)-1]
    
    else:
        return result