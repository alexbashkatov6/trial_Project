class StandardCellPipelines:

    def __init__(self):
        self.default_pipeline = [self.check_syntax_default, self.check_type, self.check_dependence_loop]
        self.name_standard_pipeline = [self.auto_name, self.check_syntax_name]
        self.common_splitter_pipeline = [self.check_syntax_common_splitter]
        self.bool_splitter_pipeline = [self.check_syntax_bool_splitter]

    @staticmethod
    def auto_name(cell):
        return cell

    @staticmethod
    def check_syntax_name(cell):
        return cell

    def check_syntax_default(self, cell):
        return cell

    def check_syntax_common_splitter(self, cell):
        return cell

    def check_syntax_bool_splitter(self, cell):
        return cell

    def check_type(self, cell):
        return cell

    def check_dependence_loop(self, cell):
        return cell

    # default_pipeline = [check_syntax_default, check_type, check_dependence_loop]

    # def name_standard_pipeline


SCP = StandardCellPipelines()

i=0
for func in SCP.default_pipeline:
   i = func(i)
print('i = ',i)