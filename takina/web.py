from flask import Flask, request, redirect
import asyncio

app = Flask(__name__)

@app.route("/callback")
def mal_callback():
    code = request.args.get("code")
    discord_id = request.args.get("state")

    # Call the bot's method to handle the OAuth2 callback asynchronously
    asyncio.ensure_future(bot.get_cog("MAL_Linking_System").handle_oauth2_callback(code, discord_id))

    return redirect("https://orangc.xyz")
