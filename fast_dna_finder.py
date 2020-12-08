import math
import subprocess
import tempfile
from enum import Enum
import os
from collections import namedtuple

LoadingStatus = Enum("LoadingStatus", "not_loaded loading loaded")

Index = namedtuple("Index", "position line_no")


class FastDnaFinder:
    """
    This dna finder uses bash tools to divide the file into the smallest
    possible genes (anything that starts with A*11) to lines, then sorting
    those lines and doing a binary search over this file to find where the gene
    starts.
    If the gene does not contain A*11 inside itself we are done and we will
    know by the search that the gene exists. If the gene contains A*11 we will
    need to follow the next lines in the file to make sure that the rest of
    the gene found matches, this is done using the `follow_chain` method which
    looks for the next line by the index.
    """

    def __init__(self, dnafilepath, use_temp_dir=True):
        self.dnafilepath = dnafilepath
        self.is_loading = LoadingStatus.not_loaded
        self.indexes = []
        if use_temp_dir:
            self.tempdir = tempfile.mkdtemp()
        else:
            self.tempdir = "."
        self.tempfile = os.path.join(self.tempdir, "sorted_data")

    def start_loading(self, process_file=True):
        """
        The precalculation is actually pretty awesome, I wanted to not load the
        file into memory and sort it, the easiest way to do it is using the
        `sort` linux command, and if we are already using prewritten tools to
        avoid loading the file into memory I can use other linux tools to preprocess
        the file. This is where `perl` and `awk` come in to break the file into
        lines by gene parts and to add line numbers.

        The flow is as follows:
        perl - Use regex to add \n after everything that starts with A*11 and ends with A*11
        awk - number the lines so we can follow the chain later
        save the file to disk so we can sort faster
        sort - sort the file by the gene to allow for binary search
        the output file is a "csv" with the first column a gene part and the second the original line number

        Inside the python program we go over the file and save the indexes so we can quickly seek into them
        when searching, I also save the original line number so when following the chain we can do reverse
        lookup and find position in the sorted file by the original line number.
        """
        if self.is_loading != LoadingStatus.not_loaded:
            raise Exception("Can't load gene file twice")
        self.is_loading = LoadingStatus.loading
        unsorted_data_path = os.path.join(self.tempdir, "unsorted_data")
        if process_file:
            self.process_file_shell(unsorted_data_path)

        with open(self.tempfile) as f:
            position = 0
            for line in f:
                original_line_number = line.split(",")[1]
                index = position
                self.indexes.append(Index(index, original_line_number))
                position += len(line)
        self.is_loading = LoadingStatus.loaded

    def process_file_shell(self, tempunsortedfilepath):
        subprocess.call(
            f"perl -pe 's|(AAAAAAAAAAA.+?)(?=AAAAAAAAAAA)|\\1\\n|g' {self.dnafilepath} | "
            f"awk '{{print $0 \",\" NR}}' > {tempunsortedfilepath}",
            shell=True,
        )
        subprocess.call(f"sort -o {self.tempfile} {tempunsortedfilepath}", shell=True)

    def search_gene(self, gene):
        """
        Binary serach over the file, if gene is in line return true, if the line is
        in the gene then look up the next line in the original file and check if it matches.
        """
        if self.is_loading != LoadingStatus.loaded:
            raise Exception("Did not perform initial search yet")
        with open(self.tempfile) as f:
            lo, hi = 0, len(self.indexes) - 1
            while True:
                c = math.ceil((lo + hi) / 2)
                f.seek(self.indexes[c].position)
                current_line, lineno = next(f).split(",")
                if gene in current_line:
                    return True
                if current_line.startswith(gene[:len(current_line)]):
                    if self.follow_chain(gene[len(current_line):], int(self.indexes[c].line_no), f):
                        return True
                if gene > current_line:
                    lo = c
                elif gene < current_line:
                    hi = c - 1
                if hi <= lo:
                    return False

    def follow_chain(self, gene, previous_line_no, f):
        """
        Follow through the indexes to find the rest of the gene in the data
        :param gene: rest of the gene to find
        :param previous_line_no: line number where start of gene was found
        :param f: the file handle
        """
        next_line_index = [
            idx
            for idx in self.indexes
            if int(idx.line_no) == previous_line_no + 1
        ][0]
        f.seek(int(next_line_index.position))
        current_line, current_line_number = next(f).split(",")
        if current_line.startswith(gene):
            return True
        if current_line.startswith(gene[: len(current_line)]):
            return self.follow_chain(gene[len(current_line):], int(current_line_number), f)
        return False


def run_on_windows(dna_finder):
    dna_finder.tempdir = "."
    dna_finder.tempfile = os.path.join(dna_finder.tempdir, "sorted_data")
    dna_finder.process_file_shell = lambda x: ()
    return dna_finder


if __name__ == "__main__":
    finder = FastDnaFinder("bigfile.txt")
    finder.start_loading()
    print(finder.search_gene("AAAAAAAAAAATAAATTCTT"))
    print(finder.search_gene("AAAAAAAAAAACGTTCGGTTTTAGGCAG"))
    print(finder.search_gene("AAAAAAAAAAACGTTCGGTTTAGGCAG"))
    print(finder.search_gene(
        "AAAAAAAAAAAAATTCGGATCGTGCAAATTTGTTACGGAAAAATGACTCGTTATCCGCCCAGAGTAGGCCATGGACGTTTCTAGGGCAATTTGGGCCCATGCTGCAACTTTGTGTAAATCTGAGGATATTATGTCCTCTGCGCTGTCCGGCGTTGTAACAGCCGGTTGGACTAATCCCACTTTCAATATGCAATGACGGAGATACAAGGCCCTCTGTTCCTTAAGCCCAGATTGACCTCACAGGGATATTATTTCGTTGCCCGGTCGCATGCGTCCTAAGCAGATCTATAACTGTTGCGTCAAGTAAGCTGTAAAAAAAAAAAGGAGTTGCCCGGTACTGCACCCTTTGCAAAATTACGCACAGTTCACTAGGCGGCGCCAATACCCGTGGGACTTTACAGCCCGATTGCTGACATACCATGTGGTTGGACTGGAAAAAAAAAAAGTGAAAACCAAACCCAATAATTGAGATCGGGGGAACCTTTATGTGGGATTAACAAAAAAAAAAATAAATTCTTAAAAAAAAAAAATATTCCAGGCCAAAAAAAAAAATACACCCGAAAAAAAAAAAAGGTATTCCTGCCCAGTAGAAGAGTCGGAACCTGACTCAAAAAAAAAAAATGAATTGATCTCAAATTGTGATCGCGGCGCTGGGGGTCGGGGGAATCCTCCACTACCGCGGAGAGGCGTCTTCCGGCTCAAGGTGACTATCTCGATCTATCGTCTAAGGACGACACTAACCCGGGGAGAAGGAATTTTCAAAGCGCCAGGTCGCTCGGTACATGACTGCCCTTCTTCCGCAAGAATGTCTGGATCAATTTCGATGAATAACTGATCCATGACGGTTACGCGCGAAGATGCCATTCTACTAATCATGACAGTATACTCAAACAAACCCTCAATCAGTCGCGAAGAGATGGGTTCTCTGACCAAACCCCCAGACCCTTAAACGTCAGAGTTGGGTCACTTATCTCACTGAAAAAAAAAAAGGGCCAGGATAACGA"))
