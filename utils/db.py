from sqlalchemy import Column, Integer, String, create_engine, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Data(Base):
    __tablename__ = 'data'
    id = Column(Integer, primary_key=True)
    func = Column(Integer)
    data_id = Column(Integer)
    data_key = Column(String(100))
    data_value = Column(Float)
    data_time = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return "<Data Record(data_id='{}', data_key='{}', data_value='{}', time={})>".format(self.data_id,
                                                                                             self.data_key,
                                                                                             self.data_value,
                                                                                             self.data_time)


class DataBase:
    def __init__(self, db_name):
        self.db_name = db_name

        self.engine = create_engine('sqlite:///record/{}.db'.format(db_name))
        # self.engine = create_engine('sqlite:///{}.db'.format(db_name))
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_data(self, d: Data):
        self.session.add(d)
        self.session.commit()


    def query_data(self, id, key, n):
        res = self.session.query(Data).filter(Data.data_id == id, Data.data_key == key).order_by(
            Data.data_time.desc()).limit(n).all()
        res.reverse()
        return res

    def close(self):
        self.session.close()


if __name__ == '__main__':
    d = DataBase("test")
    r = d.query_data(0x01, "pv_input_voltage", 10)
    print(r)
