class DnaFinderNaive:
    def __init__(self, dnafilepath):
        self.dnafilepath = dnafilepath

    def search_gene(self, gene):
        """
        This is the O(n) solution (even worse depending on how the filesystem implements read(1))
        """
        with open(self.dnafilepath, "r") as f:
            index = 0
            while r := f.read(1):
                if r == gene[index]:
                    index += 1
                else:
                    index = 0
                if index == len(gene):
                    return True
            return False

    def start_loading(self, finished_callback):
        finished_callback()