
import os
import struct
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv


# ==========================================
# CONFIGURAÇÕES
# ==========================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

MUSIC_FILE = Path(__file__).parent / "music" / "musica.mp3"

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"


# ==========================================
# CARREGAMENTO DO OPUS
# ==========================================

opus_file = (
    Path(discord.__file__).parent
    / "bin"
    / (
        "libopus-0.x64.dll"
        if struct.calcsize("P") == 8
        else "libopus-0.x86.dll"
    )
)

discord.opus.load_opus(str(opus_file))

print("Opus carregado:", discord.opus.is_loaded())


# ==========================================
# CONFIGURAÇÃO DO BOT
# ==========================================

class MusicBot(commands.Bot):

    async def setup_hook(self):
        await self.tree.sync()
        print("Comandos sincronizados!")


intents = discord.Intents.default()

bot = MusicBot(
    command_prefix="!",
    intents=intents
)


# ==========================================
# EVENTO DE INICIALIZAÇÃO
# ==========================================

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")


# ==========================================
# COMANDO /BIGAJAIRA
# ==========================================

@bot.tree.command(
    name="bigajaira",
    description="Toca a música no canal de voz"
)
async def tocar(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    try:

        # Verifica se está em um servidor
        if interaction.guild is None:
            await interaction.followup.send(
                "Este comando só funciona em servidores."
            )
            return

        # Verifica se o usuário está em um canal de voz
        if not interaction.user.voice:
            await interaction.followup.send(
                "Você precisa estar em um canal de voz."
            )
            return

        # Verifica se o arquivo existe
        if not MUSIC_FILE.exists():
            print(f"Arquivo não encontrado: {MUSIC_FILE}")

            await interaction.followup.send(
                "Arquivo de música não encontrado."
            )
            return

        guild = interaction.guild
        channel = interaction.user.voice.channel

        voice_client = guild.voice_client

        # Verifica se já existe música tocando
        if voice_client and (
            voice_client.is_playing() or voice_client.is_paused()
        ):
            await interaction.followup.send(
                "Já existe uma música tocando!"
            )
            return

        # Conecta ou move o bot para o canal
        if voice_client is None:
            voice_client = await channel.connect()

        elif voice_client.channel != channel:
            await voice_client.move_to(channel)

        # Configura o áudio
        audio = discord.FFmpegPCMAudio(
            str(MUSIC_FILE),
            executable=FFMPEG_PATH,
            before_options="-nostdin",
            options="-vn"
        )

        # Diagnóstico ao finalizar a reprodução
        def audio_finished(error):
            if error:
                print(f"ERRO NA REPRODUÇÃO: {repr(error)}")
            else:
                print("Reprodução finalizada sem erro.")

        # Diagnóstico antes de iniciar
        print("Estado antes de play():")
        print("Conectado:", voice_client.is_connected())
        print("Tocando:", voice_client.is_playing())
        print("Pausado:", voice_client.is_paused())
        print("Player existente:", voice_client._player is not None)

        # Inicia a reprodução UMA ÚNICA VEZ
        voice_client.play(
            audio,
            after=audio_finished
        )

        # Diagnóstico após iniciar
        print("Fonte de áudio:", type(audio).__name__)
        print("Player ativo:", voice_client.is_playing())
        print("Conectado:", voice_client.is_connected())
        print("Tocando:", voice_client.is_playing())
        print("Pausado:", voice_client.is_paused())
        print("Canal:", voice_client.channel.name)

        print("Player iniciado!")

        await interaction.followup.send(
            f"🎵 Reproduzindo música em **{channel.name}**!"
        )

    except Exception as error:

        print(f"Erro ao reproduzir: {repr(error)}")

        await interaction.followup.send(
            "Não consegui iniciar a reprodução. Confira o terminal."
        )


# ==========================================
# COMANDO /PARAR
# ==========================================

@bot.tree.command(
    name="parar",
    description="Interrompe a música"
)
async def parar(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    voice_client = (
        interaction.guild.voice_client
        if interaction.guild
        else None
    )

    if voice_client is None or not (
        voice_client.is_playing() or voice_client.is_paused()
    ):
        await interaction.followup.send(
            "Não há música tocando."
        )
        return

    voice_client.stop()

    await interaction.followup.send(
        "⏹️ Música interrompida!"
    )


# ==========================================
# COMANDO /SAIR
# ==========================================

@bot.tree.command(
    name="sair",
    description="Desconecta o bot do canal"
)
async def sair(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    voice_client = (
        interaction.guild.voice_client
        if interaction.guild
        else None
    )

    if voice_client is None:
        await interaction.followup.send(
            "Não estou conectado a nenhum canal."
        )
        return

    await voice_client.disconnect()

    await interaction.followup.send(
        "👋 Desconectado do canal de voz!"
    )


# ==========================================
# INICIALIZAÇÃO
# ==========================================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN não encontrado no arquivo .env"
    )

bot.run(TOKEN)
    