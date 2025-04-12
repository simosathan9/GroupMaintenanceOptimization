import pandas as pd

class InstanceReader:
    def __init__(self, path):
        self.path = path

    def read_data_xslx(self):
        return pd.read_excel(self.path)

    def read_data_csv(self):
        return pd.read_csv(self.path)