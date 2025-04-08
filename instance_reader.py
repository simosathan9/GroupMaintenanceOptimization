import pandas as pd

class InstanceReader:
    def __init__(self, path):
        self.path = path

    def read_data(self):
        return pd.read_excel(self.path)