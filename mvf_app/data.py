import os
import cryoemtools.relionstarparser as rsp


class MotionCtfData:
    def __init__(self, path):
        self.path = path
        self.data_file = None
        self.data_count = 0
        self.data = None

    def update(self):
        if not os.path.isfile(self.path):
            return False
        with open(self.path, 'r') as hint_file:
            data_file, data_count = hint_file.readline().strip().split()
            data_file = os.path.join(os.path.dirname(self.path), data_file)
            data_count = int(data_count)
        if data_count != self.data_count or data_file != self.data_file:
            data = rsp.read_star(data_file, block_list=['micrographs'], flatten=True)
            self.data_file = data_file
            self.data_count = data_count
            self.data = data
            return True
        else:
            return False

    def to_datatable_format(self, columns):
        if self.data:
            return [{col: self.data[col][i] for col in columns} for i in range(len(self.data[columns[0]]))]
        else:
            return []
