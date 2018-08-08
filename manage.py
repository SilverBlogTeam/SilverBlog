#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys

from manage import menu

lang = None
if "LANG" not in os.environ:
    lang = "None"
if "UTF-8" not in os.environ["LANG"] and "UTF.8" not in os.environ["LANG"]:
    lang = os.environ["LANG"]
if lang is not None:
    print("The current locale is: {} .Some characters may not be displayed and processed.".format(lang))
    input("Press enter to continue.")
if __name__ == '__main__':
    if not os.path.exists("./config/page.json") or not os.path.exists("./config/menu.json"):
        print("Please execute the installation wizard first.")
        exit(1)
    if not os.path.exists("./config/system.json"):
        from manage import setting

        setting.setup_wizard()
        exit(0)

    if len(sys.argv) == 1:
        menu.use_whiptail_mode()
        exit(0)
    parser = argparse.ArgumentParser("SilverBlog management tool")
    parser.add_argument("command", help="The name of the function to execute.", )

    #new
    new_parser = parser.add_argument_group('new', "Create a new article.")
    new_parser.add_argument("-c", "--config", help="The configuration file location you want to load.", type=str)
    new_parser.add_argument("-i", "--independent", help="Generate an article that does not appear in the article list",
                            action="store_true")

    parser.add_argument_group('update', "Update article metadata.")

    upgrade_parser = parser.add_argument_group('upgrade', "Upgrade program")
    upgrade_parser.add_argument("-y", "--yes", help="Assume yes for all questions, do not ask.", action="store_true")
    parser.add_argument_group('setting', "Setting program")
    parser.add_argument_group('qrcode', "Output client qrcode.")
    #build-gh-page
    group_build_gh_page = parser.add_argument_group("build-page", "Generate static pages.")

    args = parser.parse_args()
    if args.command == "setting":
        from manage import setting
        setting.setting_menu()
        exit(0)
    try:
        menu.use_text_mode(args)
        # After hitting will exit
    except KeyboardInterrupt:
        print("User cancelled operation.")
        exit(0)
    parser.print_help()
