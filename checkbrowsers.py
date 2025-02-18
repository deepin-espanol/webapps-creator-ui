#!/usr/bin/env python3

import os
import subprocess

system_browsers = {
    "Google Chrome": [
        "/usr/bin/google-chrome",
        "/opt/google/chrome/google-chrome",
        "/usr/local/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/local/bin/google-chrome-stable"
    ],
    "Vivaldi": [
        "/usr/bin/vivaldi",
        "/opt/vivaldi/vivaldi",
        "/usr/local/bin/vivaldi",
        "/usr/local/bin/vivaldi-stable",
        "/usr/bin/vivaldi-stable"
    ],
    "Opera": [
        "/usr/bin/opera",
        "/opt/opera/opera",
        "/usr/local/bin/opera",
        "/usr/local/bin/opera-stable",
        "/usr/bin/opera-stable"
    ],
    "Brave": [
        "/usr/bin/brave-browser",
        "/opt/brave/brave-browser",
        "/usr/local/bin/brave-browser",
        "/usr/local/bin/brave-browser-stable",
        "/usr/bin/brave-browser-stable"
    ],
    "Microsoft Edge": [
        "/usr/bin/microsoft-edge",
        "/opt/microsoft/edge/microsoft-edge",
        "/usr/local/bin/microsoft-edge",
        "/usr/local/bin/microsoft-edge-stable",
        "/usr/bin/microsoft-edge-stable"
    ],
    "Deepin Browser": [
        "/usr/bin/browser"
    ]
}

flatpak_browsers = {
    "Google Chrome": "com.google.Chrome",
    "Vivaldi": "com.vivaldi.Vivaldi",
    "Opera": "com.opera.Opera",
    "Microsoft Edge": "com.microsoft.Edge"
}

linglong_browser = "org.deepin.browser"

def check_system_browsers():
    installed_browsers = []
    for browser, paths in system_browsers.items():
        for path in paths:
            if os.path.exists(path):
                installed_browsers.append(('system', browser, f"{path} --app="))
                break
    return installed_browsers

def check_flatpak_browsers():
    installed_browsers = []
    try:
        flatpak_list = subprocess.check_output(["flatpak", "list"]).decode("utf-8")
        for browser, app_id in flatpak_browsers.items():
            if app_id in flatpak_list:
                installed_browsers.append(('flatpak', browser, f"flatpak run {app_id} --app="))
    except subprocess.CalledProcessError:
        pass
    return installed_browsers

def check_linglong_browser():
    installed_browsers = []
    try:
        ll_cli_list = subprocess.check_output(["ll-cli", "list"]).decode("utf-8")
        if linglong_browser in ll_cli_list:
            installed_browsers.append(('linyaps', 'Deepin Browser', f"/usr/bin/ll-cli run {linglong_browser} -- browser --app="))
    except subprocess.CalledProcessError:
        pass
    return installed_browsers

def main():
    installed_browsers = []
    installed_browsers.extend(check_system_browsers())
    installed_browsers.extend(check_flatpak_browsers())
    installed_browsers.extend(check_linglong_browser())

    installed_browsers.append(('system', 'WebApps Browser', 'python3 /usr/share/webapps-creator-ui/webapps-creator-ui-wb.py '))

    for browser in installed_browsers:
        print(f"{browser[0]} \"{browser[1]}\" \"{browser[2]}\"")

if __name__ == "__main__":
    main()