if __name__ == '__main__':
    print("The upgrade script has changed. You need to execute the upgrade command again to update the data structure.")
    exit(0)

from common import install_module


def main():
    install_module.install_package("xpinyin")
    uninstall_dependency = input('Do you want to uninstall pypinyin now? [y/N]')
    if uninstall_dependency.lower() == 'y':
        install_module.uninstall_package("pypinyin")
    print("We modified the startup script, please redeploy the startup script.")
    print("The template format has been modified. Please upgrade the template.")