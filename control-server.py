import hashlib
import json

from flask import Flask, request

from common import file
from manage import new_post

app = Flask(__name__)


@app.route('/control/new', methods=['POST'])
def new():
    title = request.json["title"]
    content = request.json["content"]
    encode = request.json["encode"]
    system_config = json.loads(file.read_file("config/system.json"))
    hash_md5 = hashlib.md5(str(title + system_config["API_Password"]).encode('utf-8')).hexdigest()
    if encode == hash_md5 and len(content) != 0:
        name = new_post.get_name(str(title))
        file.write_file("./document/{0}.md".format(name), str(content))
        config_raw={"title":str(title),"name":name,"file":"./document/{0}.md".format(name)}
        config=json.dumps(config_raw)
        new_post.new_post_init(config, None)
        return '{"status":"ok"}'
    else:
        return '{"status":"no"}'