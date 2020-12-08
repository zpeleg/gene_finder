# Gene Finder
I have tested this using python 3.8 on windows and linux, but this does not work on windows standalone!

The script depends on being run in a bash environment to preprocess the file. I have tested it under WSL to do the 
file preprocessing and after that you can run in "windows mode" under windows.

The command to run the server is:
`python3 main.py <inputfile>`

I am also adding the data files that I used to test the program in case you do not have a linux machine available, in
this case you need to run:
`python3 main.py --windows-mode`

tbh, I did not test this thoroughly so it may break, I suggest running on a linux machine.

The server is pretty straightforward if a bit hacky, the fast dna finder has all the tricks encapsulated within and
has documentation in the file as well as to how it works.