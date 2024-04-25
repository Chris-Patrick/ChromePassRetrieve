### Educational Purposes Only!!

This was an example of the impacts of having a weak password on your windows machine and the impacts it can have.

# How it works

Chrome saves passwords in an elevated privileges directory in file encrypted by your windows password.

The exe uses python to take the file from the directory, then brute force the decryption and save the passwords to a file.

# Ultra Uses

The other use was to use a Flipper Zero BadUSB script to download the file from github, run the exe, decrypt passwords, then send the file to a discord webhook.
