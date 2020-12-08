from flask import Flask
from flask_restful import Resource, Api
from fast_dna_finder import FastDnaFinder, LoadingStatus
from threading import Thread
import argparse

app = Flask(__name__)
api = Api(app)

# Use this if running on preprocessed file on windows
dna_finder = FastDnaFinder("bigfile.txt", use_temp_dir=False)
# Use this if you want to run the whole process on a new file on linux
# dna_finder = DnaFinderSorted("bigfile.txt")
print("Finished loading")


class Gene(Resource):
    def get(self, gene):
        if dna_finder.is_loading != LoadingStatus.loaded:
            return {"error": "file not loaded yet"}, 500
        if not gene.startswith("AAAAAAAAAAA"):
            return {"error": "not a valid gene"}, 400
        if dna_finder.search_gene(gene):
            return {"gene_found": True}
        else:
            return {"gene_found": False}, 404


api.add_resource(Gene, "/gene/<string:gene>")


def main():
    parser = argparse.ArgumentParser(description='Run dna server')
    parser.add_argument("inputfile", type=str, help="the dna file")
    parser.add_argument("--windows-mode", action="store_true", default=False,
                        help="run in windows mode, does not run preprocessing"
                             "and assumes that the processed file exists in "
                             "the current directory")
    arguments = parser.parse_args()
    # a bit hacky but I really should stop working on this, if I had infinite time I would find how to inject this
    # as a dependency
    global dna_finder
    dna_finder = FastDnaFinder(arguments.inputfile, not arguments.windows_mode)

    def load():
        from time import sleep
        sleep(10)
        dna_finder.start_loading(process_file=not arguments.windows_mode)
        print("Loaded")

    t = Thread(target=load)
    t.start()
    app.run(debug=True)
    t.join()


if __name__ == "__main__":
    main()
