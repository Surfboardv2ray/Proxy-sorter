import shutil

from git import Repo
from dotenv import load_dotenv
import os

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', 'default_token')
REPO = os.getenv('REPO', 'Surfboardv2ray/Proxy-sorter')
IS_DEBUG = bool(int(os.getenv('DEBUG_MODE', '0')))


if os.path.exists("./repo/.git"):
    repo = Repo("./repo/")
else:
    repo = Repo.clone_from(
        "https://mrm:{TOKEN_GITHUB}@github.com/{REPO}".format(TOKEN_GITHUB=GITHUB_TOKEN, REPO=REPO), "./repo")

with repo.config_reader() as git_config:
    try:
        mainGitEmail = git_config.get_value('user', 'email')
        mainGitUser = git_config.get_value('user', 'name')
    except:
        mainGitEmail = "None"
        mainGitUser = "None"


def changeGitUserToBot():
    with repo.config_writer() as gitConfig:
        gitConfig.set_value('user', 'email', 'bot@auto.com')
        gitConfig.set_value('user', 'name', 'Bot-auto')


def resetGitUser():
    global mainGitUser, mainGitEmail
    with repo.config_writer() as gitCnf:
        gitCnf.set_value('user', 'email', mainGitEmail)
        gitCnf.set_value('user', 'name', mainGitUser)


def getLatestRowProxies():
    if not IS_DEBUG:
        repo.git.execute(["git", "fetch", "--all"])
        repo.git.execute(["git", "checkout", "remotes/origin/master", "xray/configs"])
        shutil.copytree("./repo/xray/configs/raw-url", "xray/configs/raw-url", dirs_exist_ok=True)


def getLatestActiveConfigs():
    if not IS_DEBUG:
        repo.git.execute(["git", "fetch", "--all"])
        repo.git.execute(["git", "checkout", "remotes/origin/master", "xray/configs"])
        shutil.copytree("./repo/xray/configs/xray-json", "xray/configs/xray-json", dirs_exist_ok=True)
        shutil.copytree("./repo/xray/configs/clash-meta", "xray/configs/clash-meta", dirs_exist_ok=True)


def commitPushRowProxiesFile(chanelUsername):
    if not IS_DEBUG:
        repo.git.execute(["git", "fetch", "--all"])
        repo.git.execute(["git", "reset", "--hard", "origin/master"])
        repo.git.execute(["git", "pull"])
        shutil.copytree("xray/configs/raw-url", "./repo/xray/configs/raw-url", dirs_exist_ok=True)
        repo.index.add([r'xray/configs/raw-url/*'])
        changeGitUserToBot()
        repo.index.commit('update proxies from {}'.format(chanelUsername))
        repo.remotes.origin.push()
        resetGitUser()
        print('pushed => update proxies from {}'.format(chanelUsername))


def commitPushRActiveProxiesFile():
    if not IS_DEBUG:
        repo.git.execute(["git", "fetch", "--all"])
        repo.git.execute(["git", "reset", "--hard", "origin/master"])
        repo.git.execute(["git", "pull"])
        shutil.copytree("xray/configs/xray-json", "./repo/xray/configs/xray-json", dirs_exist_ok=True)
        shutil.copytree("xray/configs/clash-meta", "./repo/xray/configs/clash-meta", dirs_exist_ok=True)
        repo.index.add([r'xray/configs/clash-meta/*'])
        repo.index.add([r'xray/configs/xray-json/*'])
        changeGitUserToBot()
        repo.index.commit('update active proxies')
        repo.remotes.origin.push()
        resetGitUser()
        print('pushed => update active proxies')
