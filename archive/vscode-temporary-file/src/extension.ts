import * as fs from "fs";
import * as os from "os";
import * as path from "path";

import * as vscode from "vscode"; // Contains the VS Code extensibility API
import * as uniqueFilename from "uniquefilename"; // Generate random file names


const extensionName = "temporary-file";
let createdTemporaryFiles = [];

// This method is called when the extension is activated
// It is activated when the command is executed for the very first time
export function activate(context: vscode.ExtensionContext) {
    const inputOptions = {
        prompt: "Set the name of the temporary file"
    };

    const home = process.platform === "win32" ? "USERPROFILE" : "HOME";

    const resolvePath = (filepath: string): string => {
        if (filepath[0] === "~") {
            return path.join(process.env[home], filepath.slice(1));
        }
        else {
            return path.resolve(filepath);
        }
    };

    const temporaryDirectory = resolvePath(
        vscode.workspace
            .getConfiguration(extensionName)
            .get("temporaryDirectory") ?? os.tmpdir());

    // The command has been defined in the package.json file
    // Now provide the implementation of the command with registerCommand
    // The commandId parameter must match the command field in package.json
    let disposable = vscode.commands.registerCommand(`${extensionName}.create`, () => {
        // The code here will be executed every time the command is executed
        vscode.window.showInputBox(inputOptions)
            .then(input => `${temporaryDirectory}${path.sep}${input}`)
            .then(filepath => uniqueFilename.get(filepath))
            .then(filepath => {
                fs.writeFile(filepath, "", err => {
                    if (err) {
                        vscode.window.showErrorMessage(err.message);
                    }
                });
                createdTemporaryFiles.push(filepath);

                vscode.workspace
                    .openTextDocument(filepath)
                    .then(vscode.window.showTextDocument);
            });
    });

    context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {
    const deleteOnExit = vscode.workspace
        .getConfiguration(extensionName)
        .get("deleteOnExit", false);

    if (deleteOnExit) {
        for (const f of createdTemporaryFiles) {
            fs.unlink(f, console.error);
        }
    }
}