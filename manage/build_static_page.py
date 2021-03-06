import asyncio
import glob
import json
import os
import shutil
import time

from common import console, file, page, post_map

system_config = dict()
page_list = list()
menu_list = list()
template_config = dict()
page_name_list = list()
i18n = dict()
static_file_dict = dict()
@asyncio.coroutine
def async_build_page(file_name, config, page_info, menu, template, i18n_config, static_file):
    return page.build_page(file_name, config, page_info, menu, template, i18n_config, static_file)

@asyncio.coroutine
def build_post_page(filename, post_name, post_list, config, menu, template, i18n_config,
                    static_file):
    file_name = os.path.basename(filename).replace(".md", "")
    console.log("Build", "Processing file: ./static_page/post/{0}.html".format(file_name))
    page_info = None
    if file_name in post_name:
        this_page_index = post_name.index(file_name)
        page_info = post_list[this_page_index]
    content = yield from async_build_page(file_name, config, page_info, menu,
                                          template, i18n_config, static_file)
    if content is not None:
        yield from file.async_write_file("./static_page/post/{0}.html".format(file_name), content)

@asyncio.coroutine
def async_json_loads(text):
    return json.loads(text)

@asyncio.coroutine
def get_system_config():
    global system_config, template_config, i18n, static_file_dict
    load_file = yield from file.async_read_file("./config/system.json")
    system_config = yield from async_json_loads(load_file)
    if len(system_config["Theme"]) == 0:
        console.log("Error",
                    "If you do not get the Theme you installed, check your configuration file and the Theme installation.")
        exit(1)
    template_location = "./templates/{0}/".format(system_config["Theme"])
    if os.path.exists(template_location + "config.json"):
        template_config_file = yield from file.async_read_file(template_location + "config.json")
        template_config = yield from async_json_loads(template_config_file)

    if os.path.exists(template_location + "cdn"):
        cdn_config_file = None
        if os.path.exists(template_location + "cdn/custom.json"):
            cdn_config_file = template_location + "cdn/custom.json"
        if cdn_config_file is None:
            cdn_config_file = template_location + "cdn/local.json"
            if system_config["Use_CDN"]:
                cdn_config_file = template_location + "cdn/cdn.json"
        cdn_file = yield from file.async_read_file(cdn_config_file)
        static_file_dict = yield from async_json_loads(cdn_file)

    if os.path.exists("./templates/{}/i18n".format(system_config["Theme"])):
        i18n_name = "en-US"
        if "i18n" in system_config and len(system_config["i18n"]) != 0:
            i18n_name = system_config["i18n"]
        i18n_filename = "./templates/{0}/i18n/{1}.json".format(system_config["Theme"], i18n_name)
        if os.path.exists(i18n_filename):
            i18n_file = yield from file.async_read_file(i18n_filename)
            i18n = yield from async_json_loads(i18n_file)

@asyncio.coroutine
def get_menu_list():
    global menu_list
    load_file = yield from file.async_read_file("./config/menu.json")
    menu_list = yield from async_json_loads(load_file)

@asyncio.coroutine
def get_page_list():
    global page_list
    load_file = yield from file.async_read_file("./config/page.json")
    page_list = yield from async_json_loads(load_file)

def load_config():
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    tasks = [get_system_config(), get_page_list(), get_menu_list()]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
    global page_list, page_name_list, menu_list, page_list
    for item in page_list:
        page_name_list.append(item["name"])
        page_list[page_list.index(item)]["time_raw"] = item["time"]
        page_list[page_list.index(item)]["time"] = str(post_map.build_time(item["time"], system_config))


def publish():
    load_config()

    if os.path.isdir("./static_page"):
        os.system("cd ./static_page && rm -r static post index && rm *.html *.xml")

    if not os.path.isdir("./static_page"):
        os.mkdir("./static_page")
    if not os.path.exists("./static_page/CNAME"):
        file.write_file("./static_page/CNAME",system_config["Project_URL"].replace("http://","").replace("https://","").replace("/",""))
    page_row = page.get_page_row(system_config["Paging"], len(page_list))
    os.mkdir("./static_page/index/")
    console.log("Build", "Processing file: ./static_page/index.html")
    content = page.build_index(1, page_row, system_config, page_list, menu_list, template_config, i18n,
                               static_file_dict)
    file.write_file("./static_page/index.html", content)
    if page_row != 1:
        file.write_file("./static_page/index/1.html", "<meta http-equiv='refresh' content='0.1; url=/'>")
        for page_id in range(2, page_row + 1):
            console.log("Build", "Processing file: ./static_page/index/{0}.html".format(str(page_id)))
            content = page.build_index(page_id, page_row, system_config, page_list, menu_list, template_config, i18n,
                                       static_file_dict)
            file.write_file("./static_page/index/{0}.html".format(str(page_id)), content)

    os.mkdir("./static_page/post/")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = [
        build_post_page(filename, page_name_list, page_list, system_config, menu_list, template_config, i18n,
                        static_file_dict)
        for filename in glob.glob("./document/*.md")]
    if len(tasks) != 0:
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()

    if not os.path.exists("./document/rss.xml"):
        from manage import build_rss
        build_rss.build_rss()
    shutil.copyfile("./document/rss.xml", "./static_page/rss.xml")

    shutil.copytree("./templates/{0}/static".format(system_config["Theme"]),
                    "./static_page/static/{0}/".format(system_config["Theme"]))
    if os.path.exists("./templates/static/user_file"):
        shutil.copytree("./templates/static/user_file", "./static_page/static/user_file")
    console.log("Success", "Create page success!")

    if not os.path.exists("./static_page/.git"):
        return True
    import git
    localtime = time.asctime(time.localtime(time.time()))
    try:
        repo = git.Repo("./static_page")
        repo.git.add("--all")
        if not repo.is_dirty():
            console.log("Success", "Build complete,No changes found.")
            return True
        repo.git.commit("-m Release time：{0}".format(localtime))
    except git.exc.GitCommandError as e:
        console.log("Error", e.args[2].decode())
        return False
    console.log("Info", "Push to the remote.")
    remote = repo.remote()
    remote.push()
    console.log("Success", "Push to the remote success.")
    return True
