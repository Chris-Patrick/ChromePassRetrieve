# Educational Purposes Only!!

This was an example of the impacts of having a weak password on your windows machine and the impacts it can have.

### How it works

Chrome saves passwords in an elevated privileges directory in file encrypted by your windows password.

The exe uses python to take the file from the directory, then exploit the ecryption by utilizing Crypto API and a DECRYPT function provided by windows.

The result is then sent to a discord webhook to view the unencrypted passwords.

### Ultra Uses

The other use was to use a Flipper Zero BadUSB script to download the file from github, run the exe, decrypt passwords, then send the file to a discord webhook.

The txt files in this repo used to work with BadUSB but have not been tested in a while.
