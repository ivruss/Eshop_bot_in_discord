import sqlalchemy as db

metadata = db.MetaData()

products = db.Table('products', metadata,
                    db.Column('id', db.Integer, primary_key=True),
                    db.Column('name', db.Text, nullable=False),
                    db.Column('description', db.Text, nullable=False),
                    db.Column('duration', db.Integer),
                    db.Column('with_logging', db.Boolean, nullable=False),
                    db.Column('is_blocked', db.Boolean, nullable=False, default=False),
                    db.Column('message_after_payment', db.Text),
                    db.Column('price', db.Integer, nullable=False),
                    db.Column('creation_date', db.Text)
                    )

ticket = db.Table('ticket', metadata,
                db.Column('id', db.Integer, primary_key=True),
                db.Column('product_id', db.Integer),
                db.Column('product_name', db.Text),
                db.Column('product_price', db.Integer),
                db.Column('product_message_after_payment', db.Text),
                db.Column('ticket_channel_id', db.Integer)
                )
    
    
