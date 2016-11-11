# linker

Simple program to remove duplicate files and replace them with symbolic links.
 
Hashing function should be changed to hash the entire file and probably use a better hashing function if the files your hashing aren't expected to be totally unique in my case the first and last 1MiB was enough to create a unique hash with the data I was using this for.
