# Temporary Files

Quickly create temporary files to use as notes or running code.

Forked from `https://github.com/jgoday/vscode-createtmpfile`

## Build

```
npm install

# Create .vsix file to install in VSCode offline manually
vsce package
```

## Extension Settings
This extension has the following settings:

* `temporary-file.deleteOnExit`: boolean - removes the created files when VSCode exits
* `temporary-file.temporaryDirectory`: string - where the temporary files will be created
