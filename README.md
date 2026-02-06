To run a program/recipe for the hotplate:
0. Make sure there is a script labeled "hotplate.py" on the Desktop.
1. Open a command line window (search for "cmd" in search bar). Hit enter.
2. Change the directory to the desktop. (Do "cd Desktop" in the command line window.)

Once you have a recipe, type "python [directory\filename]" in the command line and hit Enter. The recipe should start running.
If needed, "Ctrl+C" in the command line will abort a running recipe. 

To write a recipe, open a new text file. Each line of the text file is a command with 5 numbers.
The syntax is:
[Temp,C] [Ramp,C/hr] [Stir,rpm] [Dwell,s] [Stabilize,0/1]
All arguments are required, i.e. every line must have 5 numbers.
If [Dwell] == -1, the system sets temp/stir and waits for cmd line input to continue program.
If [Temp] <= 25, the heater is shut off.
If [Stabilize] == 0, the script will not wait for the hotplate to stabilize before continuing to the dwell step.
If [Stabilize] == 1, the script will wait for the hotplate to stabilize before continuing to the dwell step.
Stir begins immediately after temp is set
Lines beginning with # are comments and are ignored by the script.

An example is labeled "PMMATransferBake.txt", stored in Desktop folder "hotplatescripts"
To run, cd to Desktop in command line and type "python hotplate.py hotplatescripts\PMMATransferBake.txt"

