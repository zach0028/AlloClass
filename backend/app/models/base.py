from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

#tout héritant de le classe DeclarativeBase est une table en BDD
#Base hérite de Declartivebase
