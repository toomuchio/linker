import sys, os, hashlib, sqlite3, argparse

######################
# Globals            #
######################
dbCon = None
dbCur = None

######################
# MAIN               #
######################
def main(cliArgs):
	global dbCon, dbCur

	try:
		dbCon = sqlite3.connect("files.db")
		dbCur = dbCon.cursor()
		print "[+] Connected to database"
	except:
		print "[-] Database connection failed"
		sys.exit(1)

	if cliArgs['link']:
		print "[+] Running in link mode on " + cliArgs['link'] + ", replacing duplicates with symbolic links..."
		recursiveScan(cliArgs['link'], True)
	elif cliArgs['scan']:
		print "[+] Running in scan mode on " + cliArgs['scan'] + ", building database of files..."
		recursiveScan(cliArgs['scan'], False)
		
	dbCon.close()
	sys.exit(0)

######################
# HASH               #
######################
def hashFile(file, blocksize=1048576):
	hash = hashlib.md5()
	with open(file, "rb") as f:
		hash.update(f.read(blocksize))
		if os.path.getsize(file) >= blocksize*2:
			f.seek(-blocksize, os.SEEK_END)
			hash.update(f.read(blocksize))
	return hash.hexdigest()

######################
# SCANNER            #
######################
def recursiveScan(path, link=False):
	global dbCon, dbCur

	try:
		dirlist = os.listdir(path)
	except:
		print "[-] Failed to list path: " + path
		return

	for file in dirlist:
		cPath = os.path.join(path, file)

		if os.path.isfile(cPath):
			dbCPath = cPath.decode("utf-8")

			if not link:
				dbCur.execute("SELECT 1 FROM files WHERE path = ?", (dbCPath,))
				if dbCur.fetchone() == None:
					try:
						dbCur.execute("INSERT INTO files VALUES(?, ?, ?)", (dbCPath, hashFile(cPath), os.path.getsize(cPath)))
						dbCon.commit()
						print "[+] Inserted entry for path: " + dbCPath
					except:
						print "[-] Failed to insert entry for path: " + dbCPath
			elif link and not os.path.islink(cPath):
				dbCur.execute("SELECT path FROM files WHERE md5 = ? AND size = ?", (hashFile(cPath), os.path.getsize(cPath)))
				result = dbCur.fetchone()
				if result == None or not os.path.isfile(result[0]):
					print "[-] Failed to locate path: " + dbCPath
				else:
					try:
						os.rename(cPath, cPath + "_link")
					except:
						print "[-] Failed to rename path: " + dbCPath
						#continue
						sys.exit(1)

					try:
						os.symlink(result[0], cPath)
					except:
						os.rename(cPath + "_link", cPath)
						print "[-] Failed to symlink path: " + dbCPath
						#continue
						sys.exit(1)

					os.unlink(cPath + "_link")
					print "[+] Symlinked path: " + dbCPath + " to path: " + result[0] + " - " + str(os.path.getsize(result[0]))

		else:
			recursiveScan(cPath, link)

######################
# RUN                #
######################
if __name__ == "__main__":
	cliParser = argparse.ArgumentParser(description = 'Simple program to remove duplicate files and replace them with symbolic links.')
	cliGroup = cliParser.add_mutually_exclusive_group(required=True)
	cliGroup.add_argument('-s', '--scan', help = 'Scan mode, build a database of files that can be linked to.')
	cliGroup.add_argument('-l', '--link', help = 'Link mode, replace files with symbolic links based on previous scans.')
	main(vars(cliParser.parse_args()))
