from shutil import copyfile
import os

directory = "."

dirs = [os.path.join(directory, sub) for sub in os.listdir(directory) if os.path.isdir(os.path.join(directory,sub))]
print("Starting .....")

for subdir in dirs:
	subdirpath = os.path.join(directory, subdir)
	index = 2
	start = 0
	for n in range(0, 5):
		files = [(os.path.join(subdirpath, file), file) for file in os.listdir(subdirpath)]
		
		print(files)
		print("---------------------")
		trainFiles = files[:start] + files[index:]
		validationFiles = files[start:index]
		
		trainDir = ".\\train" + subdir + str(n + 1)
		valDir = ".\\val" + subdir + str(n + 1)
		if not os.path.exists(trainDir):
			os.makedirs(trainDir)
		if not os.path.exists(valDir):
			os.makedirs(valDir)
		for trainfile in trainFiles:
			copyfile(trainfile[0], trainDir + "\\" + trainfile[1])

		for valfile in validationFiles:
			copyfile(valfile[0], valDir + "\\" + valfile[1])
		start = index
		index += 2
		
print("Done")