from dotenv import load_dotenv
import ast
import requests
import hashlib
import random
import re
import os
import glob
import subprocess
import atexit
import json
import yfinance
from os import path
from numpy import fromstring, array2string
from numpy.fft import fft

try:
    import mandelbrot
    import lambada
except Exception:
    from . import mandelbrot
    from . import lambada

lambada = lambada.Interpreter()


load_dotenv()

HOST = os.getenv("BYTIE_HOST") or 'http://localhost/'
PATH = os.getenv("BYTIE_PATH") or './.tmp'

message_handlers = []


def message_handler(name: str, prefix: bool = True, probability: float = 0.0):
    def decorator(func):
        def handler(message):
            if (prefix and message.startswith(name + ' ')) or (not prefix and message == name):
                msg = message[min(len(message), len(name)+1):]
                try:
                    return func(msg)
                except Exception as e:
                    return 'Beep boop! bytie is confused! ' + str(e)
            elif random.random() < probability:
                try:
                    return func(message)
                except Exception as e:
                    return 'Beep boop! bytie is confused! ' + str(e)
            return ''
        if func.__doc__ == None:
            # dev warning message
            print(
                f"Please provide a docstring for your message handler '{name}'. This will be used for help messages."
            )
            return func
        message_handlers.append({
            "name": name,
            "prefix": prefix,
            "probability": probability,
            "handler": handler,
            "help_message": func.__doc__,
            "function": func
        })
        return func

    return decorator


@message_handler("hey bytie!", prefix=False)
def bytie_handle_hey_bytie(command: str) -> str:
    "hey bytie!: I say 'Yes, sir!'"
    return "Yes, sir!"


@message_handler("ast")
def bytie_handle_ast(command: str) -> str:
    "ast ${python code} I generate abstract syntax trees"
    parsed = ast.parse(command)
    tree = ast.dump(parsed)
    return tree


@message_handler("latex")
def bytie_handle_latex(command: str) -> str:
    "latex ${equation}: I generate LaTeX equations"
    return "https://latex.codecogs.com/png.latex?" + command


@message_handler('8ball')
def bytie_handle_8ball(command: str) -> str:
    "8ball ${question} : I deeply analyze your question and give a comprehensive answer."
    eight_ball_messages = [
        "As I see it, yes.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don’t count on it.",
        "It is certain.",
        "It is decidedly so.",
        "Most likely.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Outlook good.",
        "Reply hazy, try again.",
        "Signs point to yes.",
        "Very doubtful.",
        "Without a doubt.",
        "Yes.",
        "Yes – definitely.",
        "You may rely on it.",
    ]
    number = int(hashlib.sha1(command.encode("utf-8")).hexdigest(), 16)
    return eight_ball_messages[number % len(eight_ball_messages)]


@message_handler('dadjoke', prefix=False)
def bytie_handle_dadjoke(command: str) -> str:
    "dadjoke: I prepare a top quality joke for you."
    resp = requests.get(
        "https://icanhazdadjoke.com", headers={"Accept": "application/json"}
    )
    if resp.status_code == 200:
        joke_id = resp.json()["id"]
        return f"https://icanhazdadjoke.com/j/{joke_id}.png"
    else:
        return "Couldn't get a dadjoke :("


@message_handler("say something new", prefix=False)
def bytie_handle_saysomethingnew(message: str) -> str:
    "say something new: Let me pick new things!"
    resp = requests.get("https://uselessfacts.jsph.pl/random.txt?language=en")
    if resp.status_code == 200:
        return resp.text.split("\n")[0]
    else:
        return "failatun failun failure :("


@message_handler("iplikisyin", probability=0.05)
def bytie_handle_iplikisyin(message: str) -> str:
    "iplikisyin ${message} : I show you exactly what you sound like."
    vowels = r"[aeıioöuü]"
    choice = random.choice("io")
    result = re.sub(vowels, choice, message.lower()) + " :rofl:"
    return result


@message_handler("usd", prefix=False)
def bytie_handle_dolar(message: str) -> str:
    "usd: Price of USD in Turkish Liras"
    webcontent = requests.get("https://themoneyconverter.com/USD/TRY").text
    parsed1 = webcontent.split("1 USD = ")
    dolartl = parsed1[1].split(" ")[0]
    return dolartl


@message_handler("fft?", prefix=False)
def bytie_handle_fft(message: str) -> str:
    "fft?: I tell you top secret information about fft."
    return "lib var"


@message_handler("fft")
def bytie_handle_fftCalc(xs: str) -> str:
    "fft <',' or ' ' seperated numbers>: I calculate fft of your numbers."
    if ',' in xs:
        xs = fromstring(xs, dtype=float, sep=",")
    else:
        xs = fromstring(xs, dtype=float, sep=" ")
    if xs.size > 0:
        return array2string(fft(xs), precision=2)
    else:
        return "meh"


@message_handler("mandelbrot")
def bytie_handle_mandelbrot(command: str) -> str:
    "mandelbrot ${x} ${y} ${zoom} ${iterations} ${divergence_radius} : I generate a mandelbrot image for you."
    args = command.split()
    try:
        x = float(args[0])
        y = float(args[1])
        zoom = float(args[2])
        max_iter = int(args[3])
        divergance_radius = float(args[4])
    except:
        return "Please feed a zoom and a center paramter! Also maximum number of iterations and divergence radius!"

    filename = f"image_{x}_{y}_{zoom}_{max_iter}_{divergance_radius}.png"
    filepath = f"{PATH}/{filename}"
    url = f"{HOST}/{filename}"
    if not(path.exists(filepath)):
        mandelbrot.mandelbrot(zoom=zoom, center=(
            x, y), filename=filepath, max_iter=max_iter, div_radius=divergance_radius)
    return url


@message_handler("XTRY")
def bytie_handle_XTRY(currency: str) -> str:
    "XTRY ${abbr. of currency}: Price of a currency in Turkish Liras"
    currency = currency.upper()
    r = requests.get(
        "https://api.exchangeratesapi.io/latest?base=TRY").json()["rates"]
    if currency in r:
        XTRY = 1/r[currency]
        return f"{currency}TRY: {XTRY:.2f}"
    else:
        return "Please enter a valid currency abbrevation"


@message_handler("lambada")
def bytie_lambada_command(command: str) -> str:
    "lambada {expression}: I want to be Clojure when I grow up"
    try:
        result = lambada.interprete(command)
        return result
    except BaseException as inst:
        return str(inst)


@message_handler("!xkcd")
def bytie_xkcd_command(command: str) -> str:
    "!xkcd {num}: I show you the xkcd you specified. Random xkcd for bad inputs."
    try:
        nxkcd = int(command)
        return bytie_handle_xkcd(nxkcd)
    except(ValueError, TypeError):
        return bytie_handle_randomxkcd()


def bytie_handle_xkcd(n):
    r = requests.get(f"https://xkcd.com/{n}/info.0.json")
    if r.status_code == 200:
        return r.json()["img"]
    else:
        return f"Two possibilities exist: either xkcd down or xkcd {n} does not exist. Both are equally terrifying."


def bytie_handle_randomxkcd():
    r = requests.get(f"https://xkcd.com/info.0.json")
    if r.status_code == 200:
        maxkcd = r.json()["num"]
        rnd = random.randint(1, maxkcd)
        return (bytie_handle_xkcd(rnd))
    else:
        return f"xkcd down :/"


@message_handler('bytie update and restart!', prefix=False)
def bytie_update_and_restart(message: str) -> str:
    "bytie update and restart!: Run git pull and register atexit() to restart run.sh"
    result = subprocess.run(["git", "pull"])

    def bytieatexit():
        subprocess.run(["/bin/bash", "run.sh"])

    atexit.register(bytieatexit)
    print("By by bytie!")
    exit(0)
    # Never runs.
    return "Restarting..."


@message_handler('bytie play song!', prefix=False)
def bytie_handle_play_song(message: str) -> str:
    "bytie play song!: I always forget the lyrics."
    words = ["real", "life", "just", "fantasy", "land", "escape", "open", "your", "eyes",
             "look", "sky", "see", "sea", "easy", "come", "go", "little", "high", "low", "way", "wind",
             "blow", "matter", "me", "man", "woman", "die", "born", "late", "tomorrow", "yesterday",
             "night", "morning", "sun", "moon", "hate", "like", "love", "scream", "crazy", "island",
             "ocean", "space", "distance", "hard", "easy", "darling", "break", "fast", "slow", "angry",
             "over", "house", "home", "cloud", "movement", "absent", "passion", "dance", "burn", "fruit",
             "time", "friend", "enemy", "war", "soldier", "army", "lost", "down", "beautiful", "tango",
             "girl", "start", "finish", "walk", "taste", "blue", "satin", "white", "red", "pink", "can", "cant",
             "free", "sweet", "need", "song", "heart", "soul"]
    wcnt = random.sample([3, 4], 1)[0]
    songname = " ".join(random.sample(words, wcnt))
    return f"-play {songname}"


@message_handler('bytie clean temp!', prefix=False)
def bytie_handle_clean_temp(message: str) -> str:
    "bytie clean temp!: Trig my garbage collector!"
    files = glob.glob(PATH + "/*")
    for f in files:
        os.remove(f)
    L = len(files)
    return f"I removed {L} garbage(s)"


@message_handler('bytie help!', prefix=False)
def bytie_handle_help(message: str) -> str:
    "bytie help! : Do you really need more help?"
    docs = []
    for handler in message_handlers:
        msg = handler['help_message']
        docs.append(f"\n\n            - {msg}")
    docs = "".join(docs)
    return f"Welcome, I am the bot of this channel. Try typing:{docs}"


@message_handler('python', prefix=False)
def bytie_handle_python(message: str) -> str:
    "python: I tell you the objective truth about python."
    return "python is bad, and you should feel bad."


@message_handler("stock")
def bytie_handle_stock(command: str) -> str:
    "stock {STOCKCODE}: This was implemented for max_zorin(PhD)"
    stockinfo = yfinance.Ticker(command)
    data = stockinfo.history(period="")

    if len(data) == 0:
        return "No data found: " + str(command)
    else:
        formatted = data.T.to_string(float_format='{:,.4f}'.format)
        result = "```\n" + command + "\n\n" + formatted + "\n```"
        return result


@message_handler("datetime")
def bytie_handle_datetime(command: str) -> str:
    "datetime region/location: I don't need an  watch."
    capt = requests.get(
        f"http://worldtimeapi.org/api/timezone/{command}")
    result = ""
    try:
        jsondata = json.loads(capt.text)
        result = jsondata["datetime"]
    except:
        result = "¯\_(ツ)_/¯ ney?"
    return result


@message_handler('bytie korona!', prefix=False)
def bytie_handle_covid(command: str) -> str:

    "bytie korona!: I show you daily vaka sayısı."

    url = 'https://covid19.saglik.gov.tr/TR-66935/genel-koronavirus-tablosu.html'
    content = requests.get(url).text

    try:
        rgx = r"var geneldurumjson = (\[.*?\]);//]]"
        match = re.search(rgx, content).group(1)
        data = json.loads(match)
        daily = data[0]

        res = """**{tarih}**
    * **Vaka**:  {gunluk_vaka}
    * **Test**:  {gunluk_test}
    * **Hasta**: {gunluk_hasta}
    * **Vefat**: {gunluk_vefat}
    * **İyileşen**: {gunluk_iyilesen}
    """.format(**daily)

        return res

    except Exception as e:
        return "Format değişmiş haberin yok! " + str(e) + " :/"


if __name__ == '__main__':
    @message_handler('test', prefix=True, probability=0)
    def test(message):
        "test : tests @message_handler functionality"
        return message + ', indeed.'
    while True:
        text = input("bytie> ")
        for handler in message_handlers:
            message = handler['handler'](text)
            if message:
                print(message)
